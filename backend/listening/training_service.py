# -*- coding: utf-8 -*-
"""Phase 4: 对症训练服务。

硬性约束落实:
- 训练由"已确认错因(final_tags)"或"高置信系统候选(>=0.6)"触发;
  两者都没有时不出训练推荐, 只提示先完成诊断(不无差别塞训练)。
- 训练内容只来自正式题目的真实数据(定位句/解析引文/教师标注),
  不生成未经审核的新题。教师标注优先; 机械提取的内容标注来源。
- mastered 证据链: 至少一个专项训练达标(规则层 is_training_passed) + 裸听复测答对
  + 复测期间未使用提示。证据不足保持 improved。
- question_mastery 是题目层掌握度, 禁止直接映射为错因/能力层掌握度。
"""
import re
from typing import Optional

from .models import Question
from .repository import exam_repo, student_repo
from .review_service import (
    _find_question,
    _find_unit,
    _question_events,
    _retry_state,
    _blind_retest_correct,
    _max_hint_level,
    question_candidates,
)
from . import review_service

PASS_THRESHOLD = 0.8

# 训练达标规则层(可按 training_type 扩展, 不把 score>=0.8 写死进 mastery 主流程)。
# 每条规则接收 (score, result, error_details) 返回 bool。
# 后续可扩展为 dictation 区分 keyword/chunk/full_sentence 准确率等子指标。
PASS_RULES = {
    "default": lambda score, result, error_details: bool(result)
    and (score or 0) >= PASS_THRESHOLD,
    # distractor 辨析要求精确说清每个干扰项的错误机制, 判分端已要求满分,
    # 这里与判分端保持一致(全对才算达标)。
    "distractor": lambda score, result, error_details: bool(result)
    and (score or 0) >= 1.0 - 1e-9,
    # paraphrase 配对同理(判分端要求全对)。
    "paraphrase": lambda score, result, error_details: bool(result)
    and (score or 0) >= 1.0 - 1e-9,
}


def is_training_passed(
    training_type: str,
    score: Optional[float],
    result: Optional[bool],
    error_details: Optional[list] = None,
) -> bool:
    """训练是否达标的唯一入口。mastery / 错题本一律走这里,
    不得在调用处直接写 score>=0.8。"""
    rule = PASS_RULES.get(training_type, PASS_RULES["default"])
    return bool(rule(score, result, error_details or []))


# 训练内容来源分级(Phase 5 画像证据权重的基础):
# teacher_calibrated   — 教师标注/校准过的内容, 可作为强证据
# generated_unverified — 机械提取/规则生成且未经教师校对, 只能用于练习,
#                        其结果不得单独成为强画像结论
PROVENANCE_TEACHER = "teacher_calibrated"
PROVENANCE_UNVERIFIED = "generated_unverified"

# 错因 -> 训练路径(可解释规则)
TRAINING_MAP: dict[str, list[tuple[str, str]]] = {
    "acoustic_miss": [("dictation", "声音没辨认出来 → 用三层听写校准耳朵对声音的捕捉")],
    "familiar_word_slow": [("dictation", "熟词反应慢 → 关键词听写训练声音到词义的反应速度"),
                           ("chunk", "语块反应训练缩短处理时间")],
    "linking_reduction": [("dictation", "连读弱读未识别 → 关键词/整句听写")],
    "phonetic_word_boundary": [("dictation", "词边界切分错误 → 整句听写")],
    "vocabulary_unknown": [("dictation", "词义不知道 → 先听写确认声音, 再对照定位句学词")],
    "chunk_unknown": [("chunk", "语块不熟 → 意群切分与重组训练")],
    "syntax_main_clause": [("chunk", "句法主干没抓住 → 意群切分, 先看结构再听细节")],
    "clause_relation": [("chunk", "逻辑关系误判 → 按意群重组句子, 看清逻辑连接")],
    "missed_locator": [("dictation", "定位失败 → 关键词听写, 训练对定位信号的敏感度")],
    "speaker_confusion": [("distractor", "说话人归属混淆 → 干扰项辨析: 看清每句话是谁说的")],
    "later_info_interference": [("distractor", "被后文信息带跑 → 干扰项辨析: 区分先后的信息归属")],
    "information_crosswire": [("distractor", "信息张冠李戴 → 干扰项辨析")],
    "paraphrase_missed": [("paraphrase", "同义替换没识别 → 原文与正确选项的替换配对训练")],
    "scope_shift": [("distractor", "范围扩大/缩小 → 命题逻辑辨析: 看清选项的范围边界")],
    "subject_swap": [("distractor", "主语偷换 → 命题逻辑辨析: 确认动作的发出者")],
    "object_swap": [("distractor", "对象偷换 → 命题逻辑辨析")],
    "unsupported_detail": [("distractor", "无中生有 → 干扰项辨析: 找原文依据")],
    "question_target_missed": [("distractor", "题干对象没看清 → 干扰项辨析时先复述题干问的是谁")],
    "memory_loss": [("dictation", "记忆丢失 → 听写强迫即时加工, 减少纯靠记忆")],
}

TRAINING_TITLES = {
    "dictation": "三层听写",
    "chunk": "意群切分",
    "paraphrase": "同义替换配对",
    "distractor": "干扰项辨析",
}

CONFIDENCE_TRIGGER = 0.6


# ---------- 训练触发(错因驱动) ----------


def training_plan(attempt_id: str, question_id: str) -> Optional[dict]:
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt or not attempt["submitted_at"]:
        return None
    exam = exam_repo.get(attempt["exam_id"])
    q = _find_question(exam, question_id) if exam else None
    if not q:
        return None

    diag = student_repo.get_diagnosis(attempt_id, question_id)
    final_tags = diag["final_tags"] if diag else []
    triggers: list[dict] = []

    if final_tags:
        triggers = [
            {"tag": t, "source": "已确认错因", "confidence": None}
            for t in final_tags
        ]
    else:
        cand = question_candidates(attempt_id, question_id)
        high = [c for c in (cand or {}).get("candidates", [])
                if c["confidence"] >= CONFIDENCE_TRIGGER]
        triggers = [
            {"tag": c["candidate_tag"], "source": "高置信系统候选", "confidence": c["confidence"]}
            for c in high
        ]

    if not triggers:
        return {
            "question_id": question_id,
            "available": False,
            "reason": "证据不足: 尚未确认错因, 也没有高置信候选。"
                      "请先完成错因自判(第③步), 系统才能给出对症训练。",
            "trainings": [],
        }

    seen = set()
    trainings = []
    for trig in triggers:
        for ttype, reason in TRAINING_MAP.get(trig["tag"], []):
            if ttype in seen:
                continue
            seen.add(ttype)
            trainings.append({
                "type": ttype,
                "title": TRAINING_TITLES[ttype],
                "triggered_by": trig["tag"],
                "trigger_source": trig["source"],
                "reason": reason,
            })
    return {
        "question_id": question_id,
        "available": True,
        "triggers": triggers,
        "trainings": trainings,
        # 当前有效诊断的快照, 训练结果保存时由服务端再次权威绑定
        "diagnosis_id": diag["id"] if diag else None,
        "diagnosis_revision": diag["revision"] if diag else None,
    }


# ---------- 训练内容(只取正式题目真实数据) ----------


def _key_phrases(q: Question) -> list[str]:
    from .review_service import _extract_key_phrases

    phrases = _extract_key_phrases(q)
    for p in q.teacher_annotation.paraphrase:
        src = p.get("source")
        if src and src not in phrases:
            phrases.append(src)
    for d in q.teacher_annotation.distractors:
        hook = d.get("source_hook")
        if hook and hook not in phrases:
            phrases.append(hook)
    return phrases[:6]


def _training_text(q: Question) -> tuple[Optional[str], str]:
    """训练用目标文本: 教师校准过的 evidence 优先; 否则用原始 transcript 句
    并标注 needs_review(含 OCR 噪声, 教师校对前质量受限)。"""
    if q.teacher_annotation.evidence_text:
        return q.teacher_annotation.evidence_text, "teacher_verified"
    return q.evidence_text, "needs_review"


def _text_provenance(quality: str) -> str:
    return (PROVENANCE_TEACHER if quality == "teacher_verified"
            else PROVENANCE_UNVERIFIED)


def training_provenance(q: Question, training_type: str) -> str:
    """保存训练结果时服务端权威判定的内容来源分级(不信任客户端上报)。"""
    if training_type in ("dictation", "chunk"):
        _, quality = _training_text(q)
        return _text_provenance(quality)
    if training_type == "distractor":
        # 干扰项机制只来自教师标注
        return PROVENANCE_TEACHER
    if training_type == "paraphrase":
        content = paraphrase_content(q)
        if not content:
            return PROVENANCE_UNVERIFIED
        origins = {p["origin"] for p in content["pairs"]}
        # 只要混有解析机械提取的对子, 整体降级为未校验
        return (PROVENANCE_TEACHER if origins == {"teacher_annotation"}
                else PROVENANCE_UNVERIFIED)
    return PROVENANCE_UNVERIFIED


def _norm_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def dictation_content(q: Question) -> Optional[dict]:
    evidence, quality = _training_text(q)
    phrases = _key_phrases(q)
    if not evidence and not phrases:
        return None
    levels = []
    if phrases:
        levels.append({
            "level": 1,
            "name": "关键词/短语听写",
            "instruction": "重听音频, 写出你听到的下列数量关键词/短语(顺序不限)。",
            "target_count": len(phrases),
        })
    if evidence:
        words = _norm_words(evidence)
        # 局部挖空: 每隔一个实词(长度>=4)挖空
        blank_positions = [
            i for i, w in enumerate(_norm_words(evidence)) if len(w) >= 4
        ][::2]
        levels.append({
            "level": 2,
            "name": "关键句局部挖空",
            "instruction": "重听音频, 补全定位句中被挖空的单词。",
            "blank_count": len(blank_positions),
        })
        levels.append({
            "level": 3,
            "name": "完整定位句听写",
            "instruction": "重听音频, 完整写出定位句。",
            "word_count": len(words),
        })
    return {"levels": levels, "text_quality": quality,
            "provenance": _text_provenance(quality)}


def _diff_words(expected: list[str], got: list[str]) -> tuple[float, list[dict]]:
    errors = []
    matched = 0
    for i, exp in enumerate(expected):
        g = got[i] if i < len(got) else None
        if g == exp:
            matched += 1
        else:
            errors.append({"index": i, "expected": exp, "got": g})
    for j in range(len(expected), len(got)):
        errors.append({"index": j, "expected": None, "got": got[j]})
    total = max(len(expected), len(got), 1)
    return matched / total, errors


def dictation_check(q: Question, level: int, inputs: list[str]) -> Optional[dict]:
    """按层级判分, 返回 score + 错误位置明细。"""
    if level == 1:
        targets = [_norm_words(p) for p in _key_phrases(q)]
        if not targets:
            return None
        got_words = set()
        for s in inputs:
            got_words.update(_norm_words(s))
        hits, misses = [], []
        for phrase in _key_phrases(q):
            words = _norm_words(phrase)
            if words and all(w in got_words for w in words):
                hits.append(phrase)
            else:
                misses.append(phrase)
        total = len(hits) + len(misses)
        score = len(hits) / max(total, 1)
        return {
            "score": round(score, 3),
            "result": score >= PASS_THRESHOLD,
            "error_details": [
                {"phrase": m, "problem": "未写出"} for m in misses
            ],
            "answer": {"phrases": _key_phrases(q)},
        }
    evidence, quality = _training_text(q)
    if not evidence:
        return None
    expected = _norm_words(evidence)
    if level == 2:
        got = _norm_words(" ".join(inputs))
        blank_idx = [i for i, w in enumerate(expected) if len(w) >= 4][::2]
        exp_subset = [expected[i] for i in blank_idx]
        score, errors = _diff_words(exp_subset, got)
        for e in errors:
            if e["index"] < len(blank_idx):
                e["position_in_sentence"] = blank_idx[e["index"]]
        return {
            "score": round(score, 3),
            "result": score >= PASS_THRESHOLD,
            "error_details": errors,
            "answer": {"evidence_text": evidence, "blank_positions": blank_idx},
        }
    # level 3 整句
    got = _norm_words(" ".join(inputs))
    score, errors = _diff_words(expected, got)
    return {
        "score": round(score, 3),
        "result": score >= PASS_THRESHOLD,
        "error_details": errors,
        "answer": {"evidence_text": evidence},
    }


def chunk_content(q: Question) -> Optional[dict]:
    evidence, quality = _training_text(q)
    if not evidence:
        return None
    # 机械切分: 按逗号与常见连接词(规则生成, 标注来源)
    parts = re.split(
        r"\s*(,|\b(?:because|so|but|and|when|if|that|which|who)\b)\s+",
        evidence, flags=re.I,
    )
    chunks: list[str] = []
    buf = ""
    for p in parts:
        if p is None:
            continue
        if re.fullmatch(r"[,]|because|so|but|and|when|if|that|which|who", p.strip(), re.I):
            buf = (buf + " " + p.strip()).strip()
        else:
            if buf:
                chunks.append((buf + " " + p.strip()).strip())
            else:
                chunks.append(p.strip())
            buf = ""
    if buf:
        chunks.append(buf)
    chunks = [re.sub(r"\s+", " ", c).strip(" ,.") for c in chunks if c.strip(" ,.")]
    if len(chunks) < 2:
        return None
    import random

    order = list(range(len(chunks)))
    random.Random(q.id).shuffle(order)  # 固定种子, 同题顺序稳定
    return {
        "instruction": "把打乱的意义块按原文顺序排列(重听音频后操作)。",
        "chunks": [chunks[i] for i in order],
        "shuffled_order": order,  # 前端回传排列时按此还原
        "source": "rule_generated_from_evidence_text",
        "text_quality": quality,
        "provenance": _text_provenance(quality),
    }


def chunk_check(q: Question, submitted_order: list[int]) -> Optional[dict]:
    content = chunk_content(q)
    if not content:
        return None
    shuffled = content["shuffled_order"]
    # submitted_order: 学生把 shuffled 后的块排成的顺序(元素为 shuffled 下标)
    correct_positions = 0
    errors = []
    n = len(shuffled)
    for pos, shuffled_idx in enumerate(submitted_order):
        if shuffled_idx >= len(shuffled):
            continue
        original_idx = shuffled[shuffled_idx]
        if original_idx == pos:
            correct_positions += 1
        else:
            errors.append({
                "position": pos,
                "placed_chunk": content["chunks"][shuffled_idx],
                "expected_position": original_idx,
            })
    score = correct_positions / max(n, 1)
    return {
        "score": round(score, 3),
        "result": score >= PASS_THRESHOLD and len(errors) == 0,
        "error_details": errors,
        "answer": {"evidence_text": q.evidence_text},
    }


def paraphrase_content(q: Question) -> Optional[dict]:
    pairs = []
    for p in q.teacher_annotation.paraphrase:
        if p.get("source") and p.get("option"):
            pairs.append({
                "source": p["source"],
                "option": p["option"],
                "origin": "teacher_annotation",
            })
    # 机械补充: 解析中"X 项是对录音中 Y 的同义转述/概括转述"
    if q.source_explanation:
        for m in re.finditer(
            r"([A-D])\s*\)?\s*项?是对录音中?([A-Za-z][A-Za-z'\-\s]{2,80}?)的(同义|概括)?转述",
            q.source_explanation,
        ):
            src = m.group(2).strip(" ,，。")
            if src and not any(p["source"] == src for p in pairs):
                pairs.append({
                    "source": src,
                    "option": m.group(1),
                    "origin": "extracted_from_explanation",
                })
    if not pairs:
        return None
    option_texts = {
        o["label"]: o["text"]
        for o in (opt.model_dump() for opt in q.options)
    }
    origins = {p["origin"] for p in pairs}
    return {
        "instruction": "把左侧原文表达与右侧正确选项含义配对, 体会同义替换。",
        "pairs": [
            {**p, "option_text": option_texts.get(p["option"])}
            for p in pairs
        ],
        "options": [{"label": k, "text": v} for k, v in option_texts.items()],
        "provenance": (PROVENANCE_TEACHER if origins == {"teacher_annotation"}
                       else PROVENANCE_UNVERIFIED),
    }


def paraphrase_check(q: Question, answers_map: dict[str, str]) -> Optional[dict]:
    content = paraphrase_content(q)
    if not content:
        return None
    errors = []
    correct = 0
    for p in content["pairs"]:
        got = answers_map.get(p["source"])
        if got == p["option"]:
            correct += 1
        else:
            errors.append({
                "source": p["source"],
                "expected_option": p["option"],
                "got": got,
            })
    total = len(content["pairs"])
    score = correct / max(total, 1)
    return {
        "score": round(score, 3),
        "result": score >= 1.0 - 1e-9,
        "error_details": errors,
        "answer": {"pairs": content["pairs"]},
    }


def distractor_content(q: Question) -> Optional[dict]:
    ds = q.teacher_annotation.distractors
    if not ds:
        return None
    # 机制候选池: 该题登记的全部 logic + 常见干扰
    pool = sorted({tag for d in ds for tag in d.get("logic", [])})
    return {
        "instruction": (
            "对每个干扰项: 先复述它说了什么, 再选择它的错误机制。"
            "只有同时说清'错在哪里'才算完成。"
        ),
        "distractors": [
            {"option": d["option"], "source_hook": d.get("source_hook")}
            for d in ds
        ],
        "mechanism_pool": pool,
        "provenance": PROVENANCE_TEACHER,
    }


def distractor_check(q: Question, selections: dict[str, list[str]]) -> Optional[dict]:
    ds = q.teacher_annotation.distractors
    if not ds:
        return None
    errors = []
    correct = 0
    for d in ds:
        want = set(d.get("logic", []))
        got = set(selections.get(d["option"], []))
        if got and got == want:
            correct += 1
        else:
            errors.append({
                "option": d["option"],
                "expected": sorted(want),
                "got": sorted(got),
                "note": d.get("note"),
            })
    total = len(ds)
    score = correct / max(total, 1)
    return {
        "score": round(score, 3),
        "result": score >= 1.0 - 1e-9,
        "error_details": errors,
    }


# ---------- 裸听复测 + mastered 证据链 ----------


def blind_retest(attempt_id: str, question_id: str, answer: str) -> Optional[dict]:
    """裸听复测: 只返回对错。复测期间(上次训练完成后起算)有提示则标记。"""
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt or not attempt["submitted_at"]:
        return None
    exam = exam_repo.get(attempt["exam_id"])
    q = _find_question(exam, question_id) if exam else None
    if not q or not q.correct_answer:
        return None

    events = _question_events(
        student_repo.list_behavior_events(attempt_id), question_id
    )
    # 复测纯度: 最近一次训练完成后没有再打开提示
    trainings = student_repo.list_training_results(
        attempt["student_id"], question_id
    )
    last_train_at = trainings[-1]["completed_at"] if trainings else None
    hints_after_training = 0
    if last_train_at:
        hints_after_training = sum(
            1
            for e in events
            if e["event_type"] == "hint_open"
            and (e["server_at"] or "") > last_train_at
        )
    is_correct = answer.strip().upper() == q.correct_answer
    student_repo.add_behavior_events(
        attempt["student_id"],
        attempt_id,
        [
            {
                "question_id": question_id,
                "event_type": "blind_retest",
                "payload": {
                    "value": answer.upper(),
                    "is_correct": is_correct,
                    "hints_during_retest": hints_after_training,
                    "scope": "unit_level_relisten(题目级时间戳待校准)",
                },
                "client_at": None,
            }
        ],
    )
    return {
        "is_correct": is_correct,
        "hints_during_retest": hints_after_training,
        "note": "本次复测为整段 Unit 复听, 无原文/关键词/历史答案/错因标签展示。",
    }


def question_mastery(ans: Optional[dict], q_events: list[dict],
                     trainings: list[dict]) -> str:
    """**题目层** 掌握度(question mastery)。mastered 最低标准:
    1. 至少一个针对性训练达标(由 is_training_passed 规则层判定)
    2. 裸听复测答对
    3. 复测期间未使用提示(hints_during_retest == 0)
    证据不足一律保持 improved/reviewing, 不过度判定。

    注意: 这里 mastered 只表示"这道题完成了训练-复测闭环",
    绝不能直接映射为"该错因/能力已掌握"(cause mastery)。
    错因层掌握度需要跨题、跨时间的稳定证据, 属于 Phase 5 的独立维度。
    """
    base = review_service.derive_mastery(ans, q_events)
    if base in ("not_mistake",):
        return base
    if base == "unreviewed":
        return base

    blind_ok = False
    for e in q_events:
        if e["event_type"] == "blind_retest" and e["payload"].get("is_correct"):
            if not e["payload"].get("hints_during_retest"):
                blind_ok = True
    train_pass = any(
        is_training_passed(
            t.get("training_type", ""), t.get("score"), t.get("result"),
            t.get("error_details"),
        )
        for t in trainings
    )
    if blind_ok and train_pass:
        return "mastered"
    return base
