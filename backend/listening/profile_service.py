# -*- coding: utf-8 -*-
"""Phase 5A: 学习者画像证据引擎(Evidence Profile Engine)。

最高约束: 本模块不发明任何新的"AI 判断"。所有结论只消费
Phase 1-4 已落库的结构化证据(作答/行为事件/诊断/训练/复测),
confidence 由显式规则计算且必须可解释(reason[] + evidence_refs)。

链路: 事件 → 错因证据聚合 → 错因置信度/当前风险 → 错因掌握度
      → 能力维度(显式映射表) → 趋势 → 规则化推荐。

硬性纪律:
- 证据覆盖按 distinct question 计, 同题反复操作不虚增跨题证据;
- generated_unverified 证据不单独形成强弱项结论(只作辅助参考);
- question mastered 不直接推出 cause mastered(错因层需要跨题证据);
- 历史弱项不永久锁死: 新题上的反证(first-try 答对)能降低 current_risk;
- 画像/推荐中的每条结论都能反查 evidence_refs。
"""
from typing import Optional

from .repository import exam_repo, load_tag_dictionary, student_repo
from .review_service import (
    _find_question,
    _question_events,
    question_candidates,
)
from .training_service import (
    CONFIDENCE_TRIGGER,
    TRAINING_MAP,
    TRAINING_TITLES,
    is_training_passed,
    question_mastery,
)

# ---------- 能力维度(显式映射表, 非 LLM 自由映射) ----------

SKILL_NAMES = {
    "info_location": "信息定位",
    "speaker_tracking": "说话人/角色追踪",
    "paraphrase_recognition": "语义改写识别",
    "distractor_inhibition": "干扰信息抑制",
    "chunk_processing": "语块加工",
    "sound_text_mapping": "声音—文本映射",
    "lexical_access": "词汇与词义反应",
    "syntax_processing": "句法加工",
    "memory_retention": "短时记忆保持",
    "question_reading": "审题与任务聚焦",
}

# 一个错因可影响多个能力维度, 固定权重(每行权重和 = 1)
CAUSE_TO_SKILL: dict[str, dict[str, float]] = {
    "acoustic_miss": {"sound_text_mapping": 1.0},
    "phonetic_word_boundary": {"sound_text_mapping": 1.0},
    "linking_reduction": {"sound_text_mapping": 1.0},
    "familiar_word_slow": {"sound_text_mapping": 0.5, "lexical_access": 0.5},
    "proper_noun_number": {"sound_text_mapping": 0.6, "info_location": 0.4},
    "vocabulary_unknown": {"lexical_access": 1.0},
    "chunk_unknown": {"chunk_processing": 0.7, "lexical_access": 0.3},
    "syntax_main_clause": {"syntax_processing": 0.7, "chunk_processing": 0.3},
    "negation_comparison": {"syntax_processing": 0.6, "distractor_inhibition": 0.4},
    "reference_relation": {"syntax_processing": 0.5, "speaker_tracking": 0.5},
    "clause_relation": {"syntax_processing": 0.5, "chunk_processing": 0.5},
    "missed_locator": {"info_location": 1.0},
    "speaker_confusion": {"speaker_tracking": 1.0},
    "information_crosswire": {"speaker_tracking": 0.5, "distractor_inhibition": 0.5},
    "memory_loss": {"memory_retention": 0.7, "chunk_processing": 0.3},
    "local_without_global": {"info_location": 0.4, "chunk_processing": 0.3,
                             "memory_retention": 0.3},
    "paraphrase_missed": {"paraphrase_recognition": 1.0},
    "lexical_overlap_trap": {"paraphrase_recognition": 0.5,
                             "distractor_inhibition": 0.5},
    "subject_swap": {"distractor_inhibition": 0.6, "speaker_tracking": 0.4},
    "object_swap": {"distractor_inhibition": 0.6, "info_location": 0.4},
    "scope_shift": {"distractor_inhibition": 0.7, "paraphrase_recognition": 0.3},
    "cause_effect_swap": {"distractor_inhibition": 0.6, "syntax_processing": 0.4},
    "time_shift": {"distractor_inhibition": 0.5, "info_location": 0.5},
    "mention_vs_claim": {"distractor_inhibition": 0.6, "paraphrase_recognition": 0.4},
    "inference_overreach": {"distractor_inhibition": 0.6, "question_reading": 0.4},
    "unsupported_detail": {"distractor_inhibition": 0.7, "info_location": 0.3},
    "question_target_missed": {"question_reading": 1.0},
    "option_prediction_fail": {"question_reading": 0.6, "paraphrase_recognition": 0.4},
    "later_info_interference": {"memory_retention": 0.5, "distractor_inhibition": 0.5},
    "common_sense_guess": {"distractor_inhibition": 0.6, "question_reading": 0.4},
}

# ---------- confidence 规则参数(显式可调, 不是模型学的) ----------

W_CONFIRMED = 0.30        # 每个"已确认错因"的 distinct question
W_CANDIDATE = 0.12        # 每个"仅高置信候选"的 distinct question
W_FAILED_TRAINING = 0.08  # 每次 teacher_calibrated 训练未达标
W_COUNTER = 0.15          # 每个反证 distinct question(有该陷阱但首答即对)
MAX_PER_SOURCE = 3        # 同一来源最多计入的 distinct question 数
CONF_HIGH = 0.7
CONF_MEDIUM = 0.4
CONFIDENCE_CAP = 0.95     # 规则引擎永不给出"确定无疑"


def _trap_tags(q) -> set[str]:
    """题目层登记的典型陷阱(存在性, 不代表学生发生了)。"""
    tags: set[str] = set()
    for d in q.teacher_annotation.distractors:
        for t in d.get("logic", []):
            tags.add(t)
    return tags


def _new_bucket() -> dict:
    return {
        "confirmed": {},        # qid -> {attempt_id, revision, at}
        "candidates": {},       # qid -> {confidence, at, evidence}
        "failed_teacher": [],   # teacher_calibrated 训练未达标
        "failed_unverified": [],  # generated_unverified 训练未达标(不计入 confidence)
        "passed_trainings": [],
        "counter": {},          # qid -> {attempt_id, at} 反证
        "question_mastery": {},  # qid -> mastery
        "evidence_question_order": [],  # 首次出现顺序
    }


def _touch_question(bucket: dict, qid: str) -> None:
    if qid not in bucket["evidence_question_order"]:
        bucket["evidence_question_order"].append(qid)


def collect_cause_evidence(student_id: str) -> dict[str, dict]:
    """聚合每个学生×错因的全部结构化证据。distinct question 为最小证据单位。"""
    buckets: dict[str, dict] = {}

    def bucket(tag: str) -> dict:
        if tag not in buckets:
            buckets[tag] = _new_bucket()
        return buckets[tag]

    attempts = student_repo.list_submitted_attempts(student_id)
    for attempt in attempts:
        exam = exam_repo.get(attempt["exam_id"])
        if not exam:
            continue
        answers = {a["question_id"]: a
                   for a in student_repo.list_answers(attempt["id"])}
        all_events = student_repo.list_behavior_events(attempt["id"])
        submitted_at = attempt["submitted_at"]

        for qid, ans in answers.items():
            q = _find_question(exam, qid)
            if not q:
                continue
            q_events = _question_events(all_events, qid)
            trainings_all = student_repo.list_training_results(student_id, qid)
            trainings = [t for t in trainings_all
                         if t.get("attempt_id") == attempt["id"]]
            mastery = question_mastery(ans, q_events, trainings_all)
            first = (ans.get("first_answer") or "").upper() or None
            first_correct = bool(
                first and q.correct_answer and first == q.correct_answer
            )

            # 反证: 题目登记了该陷阱, 但学生首答即对(没被带跑)
            if first_correct:
                for tag in _trap_tags(q):
                    b = bucket(tag)
                    b["counter"][qid] = {
                        "attempt_id": attempt["id"], "at": submitted_at,
                        "question_number": q.number,
                    }

            # 已确认错因(学生层, 显式确认才进来)
            diag = student_repo.get_diagnosis(attempt["id"], qid)
            if diag:
                for tag in diag["final_tags"]:
                    b = bucket(tag)
                    b["confirmed"][qid] = {
                        "attempt_id": attempt["id"],
                        "revision": diag["revision"],
                        "at": diag["updated_at"],
                        "first_answer": ans.get("first_answer"),
                        "final_answer": ans.get("final_answer"),
                        "question_number": q.number,
                    }
                    b["question_mastery"][qid] = mastery
                    _touch_question(b, qid)

            # 高置信系统候选(排除已确认的, 避免双计)
            final_tags = set(diag["final_tags"]) if diag else set()
            if not first_correct:
                cand = question_candidates(attempt["id"], qid)
                for c in (cand or {}).get("candidates", []):
                    tag = c["candidate_tag"]
                    if tag in final_tags or c["confidence"] < CONFIDENCE_TRIGGER:
                        continue
                    b = bucket(tag)
                    prev = b["candidates"].get(qid)
                    if not prev or c["confidence"] > prev["confidence"]:
                        b["candidates"][qid] = {
                            "confidence": c["confidence"],
                            "at": submitted_at,
                            "evidence": c["evidence"],
                            "attempt_id": attempt["id"],
                            "first_answer": ans.get("first_answer"),
                            "final_answer": ans.get("final_answer"),
                            "question_number": q.number,
                        }
                    b["question_mastery"][qid] = mastery
                    _touch_question(b, qid)

            # 训练结果(按 trigger_tags 归属错因; provenance 分级)
            for t in trainings:
                passed = is_training_passed(
                    t.get("training_type", ""), t.get("score"),
                    t.get("result"), t.get("error_details"),
                )
                for tag in t.get("trigger_tags") or []:
                    b = bucket(tag)
                    rec = {
                        "id": t["id"], "type": t["training_type"],
                        "score": t.get("score"), "passed": passed,
                        "at": t["completed_at"],
                        "provenance": t.get("provenance"),
                    }
                    if passed:
                        b["passed_trainings"].append(rec)
                    elif t.get("provenance") == "teacher_calibrated":
                        b["failed_teacher"].append(rec)
                    else:
                        b["failed_unverified"].append(rec)
                    _touch_question(b, qid)
    return buckets


def _confidence_and_reason(tag: str, b: dict) -> tuple[float, str, list[dict]]:
    """规则化 confidence: 每条贡献都记录进 reason[], 可逐条反查。"""
    score = 0.0
    reason: list[dict] = []

    confirmed_qs = list(b["confirmed"].items())[:MAX_PER_SOURCE]
    if confirmed_qs:
        delta = W_CONFIRMED * len(confirmed_qs)
        score += delta
        reason.append({
            "rule": "confirmed_diagnosis",
            "delta": round(delta, 2),
            "text": f"{len(confirmed_qs)} 道不同题确认了该错因(+{delta:.2f})",
            "refs": [qid for qid, _ in confirmed_qs],
        })

    cand_only = [(qid, c) for qid, c in b["candidates"].items()
                 if qid not in b["confirmed"]][:MAX_PER_SOURCE]
    if cand_only:
        delta = W_CANDIDATE * len(cand_only)
        score += delta
        reason.append({
            "rule": "high_confidence_candidate",
            "delta": round(delta, 2),
            "text": f"{len(cand_only)} 道不同题存在高置信候选(+{delta:.2f})",
            "refs": [qid for qid, _ in cand_only],
        })

    failed_teacher = b["failed_teacher"][:MAX_PER_SOURCE]
    if failed_teacher:
        delta = W_FAILED_TRAINING * len(failed_teacher)
        score += delta
        reason.append({
            "rule": "failed_teacher_calibrated_training",
            "delta": round(delta, 2),
            "text": f"{len(failed_teacher)} 次教师校准内容的训练未达标(+{delta:.2f})",
            "refs": [t["id"] for t in failed_teacher],
        })

    counter_qs = list(b["counter"].items())[:MAX_PER_SOURCE]
    if counter_qs:
        delta = W_COUNTER * len(counter_qs)
        score -= delta
        reason.append({
            "rule": "counter_evidence",
            "delta": -round(delta, 2),
            "text": f"{len(counter_qs)} 道含该陷阱的题首答即对(-{delta:.2f})",
            "refs": [qid for qid, _ in counter_qs],
        })

    score = round(max(0.0, min(score, CONFIDENCE_CAP)), 2)
    if score >= CONF_HIGH:
        level = "high"
    elif score >= CONF_MEDIUM:
        level = "medium"
    elif score > 0:
        level = "low"
    else:
        level = "insufficient"
    return score, level, reason


def _times(b: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """(最早支持证据, 最新支持证据, 最新反证) 的 ISO 时间。"""
    support = [v["at"] for v in b["confirmed"].values()]
    support += [v["at"] for v in b["candidates"].values()]
    support += [t["at"] for t in b["failed_teacher"]]
    support = [t for t in support if t]
    counter = [v["at"] for v in b["counter"].values() if v.get("at")]
    return (
        min(support) if support else None,
        max(support) if support else None,
        max(counter) if counter else None,
    )


def _trend(b: dict) -> dict:
    """区分同题救回与跨题迁移。"""
    ev_qs = b["evidence_question_order"]
    recovered = sum(
        1 for qid in ev_qs
        if b["question_mastery"].get(qid) in ("improved", "mastered")
    )
    # 跨题迁移: 首次针对该错因的训练之后, 含该陷阱的新题首答即对
    first_train_at = min(
        [t["at"] for t in b["passed_trainings"] + b["failed_teacher"]
         + b["failed_unverified"] if t.get("at")],
        default=None,
    )
    transfer_qs = []
    if first_train_at:
        for qid, c in b["counter"].items():
            if c["at"] and c["at"] > first_train_at and qid not in ev_qs:
                transfer_qs.append(qid)
    return {
        "within_question_recovery": {
            "recovered": recovered, "total": len(ev_qs),
        },
        "cross_question_transfer": {
            "transferred": len(transfer_qs), "questions": transfer_qs,
        },
    }


def _cause_mastery(b: dict, trend: dict) -> str:
    """错因层掌握度: 与 question mastery 完全分离, 只看跨题证据。

    unknown / evidence_accumulating / improving / stable
    """
    if not b["evidence_question_order"]:
        return "unknown"
    transfer = trend["cross_question_transfer"]["transferred"]
    _, last_support, last_counter = _times(b)
    if transfer >= 2 and last_counter and (
        not last_support or last_counter > last_support
    ):
        return "stable"
    mastered_qs = sum(
        1 for m in b["question_mastery"].values() if m == "mastered"
    )
    if transfer >= 1 or (mastered_qs >= 1 and
                         trend["within_question_recovery"]["total"] > 0):
        return "improving"
    return "evidence_accumulating"


def _current_risk(conf_level: str, b: dict, cause_mastery: str) -> str:
    """当前风险可被新题反证修正, 不被历史证据永久锁死。"""
    if conf_level in ("low", "insufficient"):
        return "insufficient"
    risk = "high" if conf_level == "high" else "medium"
    _, last_support, last_counter = _times(b)
    if cause_mastery == "stable":
        return "low"
    # 最新反证晚于最新支持证据 → 降一级
    if last_counter and (not last_support or last_counter > last_support):
        risk = "medium" if risk == "high" else "low"
    if cause_mastery == "improving" and risk == "high":
        risk = "medium"
    return risk


def build_cause_profile(student_id: str) -> list[dict]:
    tag_dict = load_tag_dictionary()
    buckets = collect_cause_evidence(student_id)
    causes = []
    for tag, b in buckets.items():
        conf, level, reason = _confidence_and_reason(tag, b)
        trend = _trend(b)
        cm = _cause_mastery(b, trend)
        risk = _current_risk(level, b, cm)
        first_at, last_support, _ = _times(b)
        only_unverified = (
            not b["confirmed"] and not b["candidates"]
            and not b["failed_teacher"] and bool(b["failed_unverified"])
        )
        supporting = []
        for qid, v in b["confirmed"].items():
            supporting.append({
                "type": "confirmed_diagnosis", "question_id": qid,
                "attempt_id": v["attempt_id"], "revision": v["revision"],
                "first_answer": v.get("first_answer"),
                "final_answer": v.get("final_answer"),
                "question_number": v.get("question_number"),
            })
        for qid, v in b["candidates"].items():
            supporting.append({
                "type": "high_confidence_candidate", "question_id": qid,
                "attempt_id": v.get("attempt_id"),
                "confidence": v["confidence"], "evidence": v["evidence"],
                "first_answer": v.get("first_answer"),
                "final_answer": v.get("final_answer"),
                "question_number": v.get("question_number"),
            })
        for t in b["failed_teacher"] + b["failed_unverified"]:
            supporting.append({
                "type": "training_failed", "training_id": t["id"],
                "training_type": t["type"], "provenance": t["provenance"],
            })
        counter = [
            {"type": "first_try_correct_with_trap", "question_id": qid,
             "attempt_id": v["attempt_id"],
             "question_number": v.get("question_number")}
            for qid, v in b["counter"].items()
        ]
        causes.append({
            "cause_tag": tag,
            "zh": tag_dict.get(tag, {}).get("zh", tag),
            "evidence_confidence": conf,
            "confidence_level": level,
            "current_risk": risk,
            "cause_mastery": cm,
            "evidence_questions": len(b["evidence_question_order"]),
            "confirmed_questions": len(b["confirmed"]),
            "candidate_only_questions": len(
                [q for q in b["candidates"] if q not in b["confirmed"]]
            ),
            "trainings": {
                "total": len(b["passed_trainings"]) + len(b["failed_teacher"])
                + len(b["failed_unverified"]),
                "passed": len(b["passed_trainings"]),
                "teacher_calibrated": len(b["passed_trainings"])
                + len(b["failed_teacher"]),
                "generated_unverified": len(b["failed_unverified"]),
            },
            "only_unverified_evidence": only_unverified,
            "first_evidence_at": first_at,
            "last_evidence_at": last_support,
            "trend": trend,
            "reason": reason,
            "supporting_evidence": supporting,
            "counter_evidence": counter,
        })
    causes.sort(key=lambda c: (-c["evidence_confidence"], c["cause_tag"]))
    return causes


def build_skill_profile(causes: list[dict]) -> list[dict]:
    """能力维度 = 错因置信度经显式映射表的加权聚合(归一化)。"""
    skills = []
    for skill, zh in SKILL_NAMES.items():
        contribs = []
        for c in causes:
            mapping = CAUSE_TO_SKILL.get(c["cause_tag"], {})
            w = mapping.get(skill)
            if not w or c["evidence_confidence"] <= 0:
                continue
            contribs.append({
                "cause_tag": c["cause_tag"],
                "cause_zh": c["zh"],
                "weight": w,
                "cause_confidence": c["evidence_confidence"],
                "current_risk": c["current_risk"],
            })
        if not contribs:
            skills.append({
                "skill": skill, "zh": zh, "level": "insufficient",
                "score": None, "from_causes": [],
            })
            continue
        denom = sum(x["weight"] for x in contribs)
        score = round(
            sum(x["weight"] * x["cause_confidence"] for x in contribs) / denom, 2
        )
        # 风险需同时考虑 current_risk: 已稳定的错因不应拉高当前风险
        risk_adjusted = round(
            sum(
                x["weight"] * x["cause_confidence"]
                * (0.3 if x["current_risk"] == "low" else 1.0)
                for x in contribs
            ) / denom,
            2,
        )
        level = ("high_risk" if risk_adjusted >= 0.6
                 else "medium_risk" if risk_adjusted >= 0.35
                 else "low_risk")
        skills.append({
            "skill": skill, "zh": zh, "level": level,
            "score": score, "risk_adjusted_score": risk_adjusted,
            "from_causes": contribs,
        })
    order = {"high_risk": 0, "medium_risk": 1, "low_risk": 2, "insufficient": 3}
    skills.sort(key=lambda s: (order[s["level"]], -(s["score"] or 0)))
    return skills


def build_recommendations(student_id: str, causes: list[dict]) -> list[dict]:
    """规则化推荐。每条必须带 why[] + evidence_refs[], 不允许无证据推荐。"""
    recs = []
    for c in causes:
        tag = c["cause_tag"]
        refs = []
        refs += [
            {"type": "question", "id": e["question_id"],
             "attempt_id": e.get("attempt_id"),
             "question_number": e.get("question_number")}
            for e in c["supporting_evidence"] if "question_id" in e
        ]
        refs += [{"type": "training", "id": e["training_id"]}
                 for e in c["supporting_evidence"] if e["type"] == "training_failed"]
        refs += [{"type": "question", "id": e["question_id"],
                  "attempt_id": e.get("attempt_id"),
                  "question_number": e.get("question_number"),
                  "role": "counter"}
                 for e in c["counter_evidence"]]

        base = {
            "target_cause": tag,
            "target_cause_zh": c["zh"],
            "target_skill": [
                {"skill": s, "zh": SKILL_NAMES[s]}
                for s in CAUSE_TO_SKILL.get(tag, {})
            ],
        }

        # 纯反证(有该陷阱的题首答即对, 无支持证据): 正面记录, 不推荐训练
        if not c["supporting_evidence"] and c["counter_evidence"]:
            recs.append({
                **base, "priority": "observe",
                "recommendation": "含该陷阱的题首答即对, 暂未暴露该弱项, 继续观察。",
                "why": ["仅有反证(首答即对), 无支持证据"],
                "evidence_refs": refs,
            })
            continue

        if c["only_unverified_evidence"]:
            recs.append({**base, "priority": "observe",
                         "recommendation": "现有证据全部来自未经教师校验的内容, "
                                          "不足以形成结论, 仅继续观察。",
                         "why": ["generated_unverified 证据不能单独形成强弱项"],
                         "evidence_refs": refs})
            continue
        if c["confidence_level"] in ("low", "insufficient"):
            recs.append({**base, "priority": "observe",
                         "recommendation": "证据不足, 继续观察, 不下强结论。",
                         "why": [f"confidence={c['evidence_confidence']} 低于阈值"],
                         "evidence_refs": refs})
            continue
        if c["cause_mastery"] == "stable":
            recs.append({**base, "priority": "low",
                         "recommendation": "该错因已在新题上稳定表现, "
                                          "降低优先级, 间隔一段时间后复测巩固即可。",
                         "why": ["跨题迁移证据 >= 2 且无新的支持证据"],
                         "evidence_refs": refs})
            continue
        training_types = [TRAINING_TITLES[t] for t, _ in TRAINING_MAP.get(tag, [])]
        if (c["confidence_level"] == "high" and c["current_risk"] == "high"):
            recs.append({
                **base, "priority": "high",
                "recommendation": f"高优先级专项训练: {'、'.join(training_types) or '综合训练'}。",
                "why": ([r["text"] for r in c["reason"]]
                        + ["当前风险高(近期仍有支持证据)"]),
                "evidence_refs": refs,
            })
        elif c["cause_mastery"] == "improving":
            recs.append({
                **base, "priority": "medium",
                "recommendation": "巩固与迁移: 在未见过的新题上验证该错因是否真正改善。",
                "why": ["已有同题恢复或初步跨题迁移证据, 需要新题验证"],
                "evidence_refs": refs,
            })
        else:
            recs.append({
                **base, "priority": "medium",
                "recommendation": f"建议训练: {'、'.join(training_types) or '综合训练'}, "
                                  f"完成后裸听复测。",
                "why": [r["text"] for r in c["reason"]],
                "evidence_refs": refs,
            })
    order = {"high": 0, "medium": 1, "low": 2, "observe": 3}
    recs.sort(key=lambda r: order[r["priority"]])
    return recs


def build_profile(student_id: str) -> dict:
    attempts = student_repo.list_submitted_attempts(student_id)
    causes = build_cause_profile(student_id)
    skills = build_skill_profile(causes)
    recs = build_recommendations(student_id, causes)
    return {
        "student_id": student_id,
        "attempts_count": len(attempts),
        "evidence_note": (
            f"证据来自 {len(attempts)} 次已提交作答。证据覆盖以 distinct "
            "question 计; generated_unverified 内容的结果不单独形成结论。"
        ),
        "causes": causes,
        "skills": skills,
        "recommendations": recs,
    }
