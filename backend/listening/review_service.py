# -*- coding: utf-8 -*-
"""Phase 3: 复盘服务。

设计约束(硬性):
- 5 级提示逐级解锁, 服务端强制; 除教师模式外不可跳级。
- 复盘视图默认不泄露正确答案/解析; L5 解锁后才返回。
- 系统候选错因必须带 evidence[]; 证据不足返回低置信度或空列表, 不硬猜。
- 候选错因绝不在此写入 final_tags; final_tags 只能由诊断确认接口写入。
- relisten_count 只能表述为"整段 Unit 重播", 不得解释为"精准复听定位句"
  (题目级时间戳目前均为 needs_review)。
"""
import re
from typing import Optional

from .models import Question
from .repository import exam_repo, new_id, student_repo

MAX_HINT_LEVEL = 5

# ---------- 内部工具 ----------


def _find_question(exam, question_id: str) -> Optional[Question]:
    for unit in exam.units:
        for q in unit.questions:
            if q.id == question_id:
                return q
    return None


def _find_unit(exam, unit_id: str):
    for unit in exam.units:
        if unit.id == unit_id:
            return unit
    return None


def _question_events(events: list[dict], question_id: str) -> list[dict]:
    return [e for e in events if e.get("question_id") == question_id]


def _max_hint_level(events: list[dict]) -> int:
    levels = [
        int(e["payload"].get("level", 0) or 0)
        for e in events
        if e["event_type"] == "hint_open"
    ]
    return max(levels, default=0)


def _retry_state(events: list[dict]) -> dict:
    retries = [e for e in events if e["event_type"] == "retry_answer"]
    return {
        "retry_count": len(retries),
        "retry_correct": any(e["payload"].get("is_correct") for e in retries),
        "last_retry_at": retries[-1]["client_at"] if retries else None,
    }


def _blind_retest_correct(events: list[dict]) -> bool:
    """裸听复测(Phase 4 训练后隐藏提示重答)事件。"""
    return any(
        e["event_type"] == "blind_retest" and e["payload"].get("is_correct")
        for e in events
    )


def derive_mastery(ans: Optional[dict], q_events: list[dict]) -> str:
    """掌握度: unreviewed / reviewing / improved / mastered。

    规则(保守, 可解释):
    - 首答即对: not_mistake
    - 无任何复听/提示/重答行为: unreviewed
    - 有复盘行为但重答未对: reviewing
    - 重答(复听后/提示后)答对: improved
    - 裸听复测答对: mastered(需 Phase 4 训练后复测事件)
    """
    if not ans:
        return "unreviewed"
    if ans.get("is_first_correct"):
        return "not_mistake"
    if _blind_retest_correct(q_events):
        return "mastered"
    retry = _retry_state(q_events)
    if retry["retry_correct"]:
        return "improved"
    if (
        retry["retry_count"] > 0
        or _max_hint_level(q_events) > 0
        or (ans.get("relisten_count") or 0) > 0
    ):
        return "reviewing"
    return "unreviewed"


# ---------- 复盘总览(不泄露答案) ----------


def review_overview(attempt_id: str) -> Optional[dict]:
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        return None
    exam = exam_repo.get(attempt["exam_id"])
    if not exam:
        return None
    answers = {a["question_id"]: a for a in student_repo.list_answers(attempt_id)}
    events = student_repo.list_behavior_events(attempt_id)
    diagnosis_rows = {}
    conn = student_repo._conn()
    for row in conn.execute(
        "SELECT * FROM diagnoses WHERE attempt_id = ?", (attempt_id,)
    ).fetchall():
        import json as _json

        d = dict(row)
        for k in ("student_tags", "ai_tags", "final_tags"):
            d[k] = _json.loads(d[k])
        diagnosis_rows[d["question_id"]] = d

    units = []
    for unit in exam.units:
        questions = []
        for q in unit.questions:
            ans = answers.get(q.id)
            q_events = _question_events(events, q.id)
            final = (ans or {}).get("final_answer") or ""
            is_correct = bool(
                final and q.correct_answer and final.upper() == q.correct_answer
            )
            unlocked = _max_hint_level(q_events)
            retry = _retry_state(q_events)
            diag = diagnosis_rows.get(q.id)
            item = {
                "question_id": q.id,
                "number": q.number,
                "section": q.section,
                "question_text": q.question_text,
                "question_text_zh": q.question_text_zh,
                "options": [o.model_dump() for o in q.options],
                "first_answer": (ans or {}).get("first_answer"),
                "final_answer": (ans or {}).get("final_answer"),
                "is_correct": is_correct,
                "is_first_correct": bool(ans["is_first_correct"])
                if ans and ans["is_first_correct"] is not None
                else None,
                "change_count": (ans or {}).get("change_count", 0),
                "dwell_ms": (ans or {}).get("dwell_ms", 0),
                "relisten_count": (ans or {}).get("relisten_count", 0),
                "max_hint_level": unlocked,
                "retry": retry,
                "mastery": derive_mastery(ans, q_events),
                "diagnosis": {
                    "student_tags": diag["student_tags"] if diag else [],
                    "final_tags": diag["final_tags"] if diag else [],
                },
                # 题目层典型陷阱只给"存在性"标记, 具体逻辑在 L5 或诊断面板查看
                "has_teacher_annotation": bool(q.teacher_annotation.distractors),
                "review_status": q.review_status,
            }
            # 只有 L5 解锁后才带出正确答案
            if unlocked >= MAX_HINT_LEVEL:
                item["correct_answer"] = q.correct_answer
            questions.append(item)
        units.append(
            {
                "unit": unit.model_dump(exclude={"questions", "transcript"}),
                "questions": questions,
            }
        )
    return {
        "attempt": attempt,
        "exam_id": exam.id,
        "title": exam.title,
        "question_count": exam.question_count,
        "units": units,
    }


# ---------- 5 级提示(逐级解锁) ----------


def _extract_key_phrases(q: Question) -> list[str]:
    """从解析中机械提取被引用的英文短语(定位用关键词)。

    来源: source_explanation / distractor_analysis 中内嵌的英文引文。
    属于原文引用, 非 AI 生成; 提取不到的题返回空列表并由前端提示待补充。
    """
    text = " ".join(
        t for t in (q.source_explanation, q.distractor_analysis) if t
    )
    phrases = re.findall(
        r"[A-Za-z][A-Za-z'’\-]*(?:\s+[A-Za-z][A-Za-z'’\-]*){1,6}", text
    )
    seen, result = set(), []
    for p in phrases:
        p = re.sub(r"\s+", " ", p).strip()
        # 过滤残留 OCR 噪声词与过短片段
        if len(p) < 4 or p.lower() in seen:
            continue
        seen.add(p.lower())
        result.append(p)
        if len(result) >= 5:
            break
    return result


def _locator_direction(q: Question) -> dict:
    """Level 2: 定位方向。规则模板来自题干本身(非编造内容)。"""
    stem = (q.question_text or "").lower()
    directions = []
    if "woman" in stem:
        directions.append("重点听女士(W)说的话, 男士的反应只作参考")
    elif "man" in stem and "woman" not in stem:
        directions.append("重点听男士(M)说的话, 女士的反应只作参考")
    elif "speaker" in stem:
        directions.append("注意说话者的身份与整体态度")
    if any(k in stem for k in ("why", "reason")):
        directions.append("留意因果信号: because / so / that's why")
    if any(k in stem for k in ("suggest", "advise", "recommend")):
        directions.append("留意建议句式: why don't you / how about / you'd better")
    if any(k in stem for k in ("study", "research", "find")):
        directions.append("留意研究结论句, 通常出现在'研究发现/显示'之后")
    if not directions:
        directions.append("跟着题干关键词走, 留意转折(but/however)之后的内容")
    return {
        "question_focus": q.question_text_zh,
        "directions": directions,
        "key_locators": q.teacher_annotation.key_locators,
    }


def hint_content(q: Question, level: int) -> dict:
    """构造某级提示内容。不含超纲信息: L1-L3 不给句子, L4 才给定位句, L5 给全部。"""
    unit_title = None
    exam = exam_repo.get(q.exam_id)
    if exam:
        unit = _find_unit(exam, q.unit_id)
        unit_title = unit.title if unit else None

    if level == 1:
        return {
            "level": 1,
            "title": "重新听",
            "content": {
                "unit_id": q.unit_id,
                "unit_title": unit_title,
                "instruction": (
                    "重新完整听一遍本段音频, 不要看任何文字。"
                    "注意题干问的对象和逻辑关系。"
                ),
                "note": "当前为整段复听(题目级时间戳待校准), 请留意题干相关内容出现的位置。",
            },
        }
    if level == 2:
        return {
            "level": 2,
            "title": "定位方向",
            "content": _locator_direction(q),
        }
    if level == 3:
        phrases = _extract_key_phrases(q)
        return {
            "level": 3,
            "title": "关键词提示",
            "content": {
                "key_phrases": phrases,
                "note": None
                if phrases
                else "该题关键词待教师补充(needs_review)",
            },
        }
    if level == 4:
        evidence = q.evidence_text
        highlight = []
        if evidence:
            for p in _extract_key_phrases(q):
                if re.search(re.escape(p), evidence, re.I):
                    highlight.append(p)
        return {
            "level": 4,
            "title": "定位原文",
            "content": {
                "evidence_text": evidence,
                "highlight": highlight,
                "note": None
                if evidence
                else "该题定位句待教师校准(needs_review)",
                "timing_status": q.timing_status,
            },
        }
    # level 5
    return {
        "level": 5,
        "title": "完整解析",
        "content": {
            "correct_answer": q.correct_answer,
            "source_explanation": q.source_explanation,
            "distractor_analysis": q.distractor_analysis,
            "teacher_paraphrase": q.teacher_annotation.paraphrase,
            "teacher_distractors": q.teacher_annotation.distractors,
        },
    }


def unlock_hint(
    attempt_id: str, question_id: str, level: int, teacher_mode: bool = False
) -> Optional[dict]:
    """逐级解锁: level 必须 <= 已解锁最高级 + 1(教师模式除外)。"""
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt or not attempt["submitted_at"]:
        return None
    exam = exam_repo.get(attempt["exam_id"])
    if not exam:
        return None
    q = _find_question(exam, question_id)
    if not q:
        return None

    events = _question_events(
        student_repo.list_behavior_events(attempt_id), question_id
    )
    current_max = _max_hint_level(events)
    if not teacher_mode and level > current_max + 1:
        return {
            "error": "locked",
            "message": f"请先查看第 {current_max + 1} 级提示, 提示需要逐级解锁。",
            "current_max": current_max,
        }

    # 只在解锁新层级时记录事件(重复查看同级不重复计数)
    if level > current_max:
        student_repo.add_behavior_events(
            attempt["student_id"],
            attempt_id,
            [
                {
                    "question_id": question_id,
                    "event_type": "hint_open",
                    "payload": {"level": level, "teacher_mode": teacher_mode},
                    "client_at": None,
                }
            ],
        )
    return {"level": level, **hint_content(q, level)}


# ---------- 错题重答(不泄露答案) ----------


def retry_answer(attempt_id: str, question_id: str, answer: str) -> Optional[dict]:
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt or not attempt["submitted_at"]:
        return None
    exam = exam_repo.get(attempt["exam_id"])
    if not exam:
        return None
    q = _find_question(exam, question_id)
    if not q or not q.correct_answer:
        return None
    is_correct = answer.strip().upper() == q.correct_answer
    student_repo.add_behavior_events(
        attempt["student_id"],
        attempt_id,
        [
            {
                "question_id": question_id,
                "event_type": "retry_answer",
                "payload": {"value": answer.upper(), "is_correct": is_correct},
                "client_at": None,
            }
        ],
    )
    # 只返回对错, 不返回正确答案
    return {"is_correct": is_correct}


# ---------- 证据化候选错因(系统推测层, 绝不写入 final_tags) ----------


def question_candidates(attempt_id: str, question_id: str) -> Optional[dict]:
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        return None
    exam = exam_repo.get(attempt["exam_id"])
    if not exam:
        return None
    q = _find_question(exam, question_id)
    if not q:
        return None

    answers = {a["question_id"]: a for a in student_repo.list_answers(attempt_id)}
    ans = answers.get(question_id)
    q_events = _question_events(
        student_repo.list_behavior_events(attempt_id), question_id
    )
    retry = _retry_state(q_events)
    max_hint = _max_hint_level(q_events)
    relisten = (ans or {}).get("relisten_count", 0) if ans else 0
    change_count = (ans or {}).get("change_count", 0) if ans else 0
    dwell_ms = (ans or {}).get("dwell_ms", 0) if ans else 0
    first = ((ans or {}).get("first_answer") or "").upper() or None
    final = ((ans or {}).get("final_answer") or "").upper() or None

    diag = student_repo.get_diagnosis(attempt_id, question_id)
    self_tags = diag["student_tags"] if diag else []

    candidates: list[dict] = []

    def boost(candidate: dict, condition: bool, evidence_text: str, delta: float):
        if condition:
            candidate["evidence"].append(evidence_text)
            candidate["confidence"] = round(
                min(candidate["confidence"] + delta, 0.9), 2
            )

    # 规则 1: 首次选项命中题目层登记的干扰逻辑
    if first and q.correct_answer and first != q.correct_answer:
        for d in q.teacher_annotation.distractors:
            if d.get("option") == first and d.get("logic"):
                for tag in d["logic"]:
                    c = {
                        "candidate_tag": tag,
                        "confidence": 0.5,
                        "evidence": [
                            f"首次作答选择了 {first}",
                            f"选项 {first} 在该题中登记的干扰来源: {d.get('source_hook') or '见解析'}",
                        ],
                    }
                    if d.get("note"):
                        c["evidence"].append(f"干扰机制: {d['note']}")
                    boost(
                        c,
                        retry["retry_correct"] or (final == q.correct_answer and change_count > 0),
                        "复听/重答后改对, 说明信息本身可被获取, 初错更可能来自干扰",
                        0.12,
                    )
                    boost(
                        c,
                        relisten > 0,
                        "作答过程中重播过整段 Unit(题目级时间戳待校准, 无法确认是否精准复听定位句)",
                        0.05,
                    )
                    boost(
                        c,
                        tag in self_tags,
                        "学生自判包含相同错因, 与系统推测一致",
                        0.1,
                    )
                    candidates.append(c)

    # 规则 2: 复听后改对但无题目层登记 -> 定位/声音层低置信候选
    if (
        not candidates
        and first
        and q.correct_answer
        and first != q.correct_answer
        and final == q.correct_answer
        and (relisten > 0 or retry["retry_correct"])
    ):
        candidates.append(
            {
                "candidate_tag": "missed_locator",
                "confidence": 0.35,
                "evidence": [
                    f"首次选择 {first} 错误, 复听/重答后改为正确答案",
                    "该题暂无教师登记的干扰项逻辑, 证据强度有限",
                ],
            }
        )

    # 规则 3: 无复听的多次改答案 / 极短停留 -> 仓促作答(低置信)
    if first != final and change_count >= 2 and relisten == 0:
        candidates.append(
            {
                "candidate_tag": "rushed_decision",
                "confidence": 0.3,
                "evidence": [
                    f"作答过程中修改答案 {change_count} 次, 且期间未重播音频",
                ],
            }
        )
    if first and q.correct_answer and first != q.correct_answer and 0 < dwell_ms < 5000:
        candidates.append(
            {
                "candidate_tag": "rushed_decision",
                "confidence": 0.25,
                "evidence": [
                    f"该题停留时间仅约 {round(dwell_ms / 1000, 1)} 秒即作出错误选择",
                ],
            }
        )

    # 规则 4: 多次重播仍未答对 -> 声音辨识层低置信候选
    if (
        relisten >= 2
        and q.correct_answer
        and final
        and final != q.correct_answer
        and not retry["retry_correct"]
    ):
        candidates.append(
            {
                "candidate_tag": "acoustic_miss",
                "confidence": 0.3,
                "evidence": [
                    f"整段 Unit 重播 {relisten} 次后仍未答对",
                    "可能声音层面未辨识, 建议用听写训练验证(证据不足, 仅低置信提示)",
                ],
            }
        )

    # 学生自判有而系统无证据的, 不生成候选(诚实: 系统没证据就不猜)
    note = None
    if not candidates:
        note = "证据不足, 暂无法推测候选错因。请结合自判与分级提示定位问题。"

    candidates.sort(key=lambda c: -c["confidence"])
    return {
        "question_id": question_id,
        "candidates": candidates,
        "note": note,
        "disclaimer": "以上仅为基于行为证据的候选推测, 需学生自判/教师确认后才成为最终错因。",
        "question_level_traps": [
            {
                "option": d.get("option"),
                "logic": d.get("logic", []),
                "source_hook": d.get("source_hook"),
            }
            for d in q.teacher_annotation.distractors
        ],
    }
