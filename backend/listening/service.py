# -*- coding: utf-8 -*-
"""业务逻辑: 套题摘要、作答判分、复盘视图、错题与画像聚合。

AI 不可用也能工作的部分全部在此; 任何 AI 派生数据只读题库中的
ai_annotation 字段(带 review_status), 不在线生成。
"""
from typing import Optional

from .models import Exam, ExamSummary, Question
from .repository import exam_repo, student_repo

# 复盘接口才允许返回的敏感字段; 考试模式下必须剥离
_SENSITIVE_FIELDS = (
    "correct_answer",
    "source_explanation",
    "distractor_analysis",
    "evidence_text",
)


def exam_summaries(student_id: str = "anonymous") -> list[ExamSummary]:
    summaries = []
    for exam in exam_repo.list():
        latest = student_repo.latest_attempt_for_exam(student_id, exam.id)
        summaries.append(
            ExamSummary(
                id=exam.id,
                exam_type=exam.exam_type,
                title=exam.title,
                year=exam.year,
                month=exam.month,
                set_no=exam.set_no,
                duration_ms=exam.duration_ms,
                question_count=exam.question_count,
                section_count=len({u.section for u in exam.units}),
                has_audio=exam_repo.audio_file(exam.id) is not None,
                completed=latest is not None,
                last_score=latest["score"] if latest else None,
                last_submitted_at=latest["submitted_at"] if latest else None,
            )
        )
    return summaries


def _question_public(q: Question) -> dict:
    """考试模式用: 剥离答案与解析。"""
    data = q.model_dump()
    for field in _SENSITIVE_FIELDS:
        data.pop(field, None)
    data.pop("teacher_annotation", None)
    data.pop("ai_annotation", None)
    return data


def exam_detail(exam_id: str) -> Optional[dict]:
    exam = exam_repo.get(exam_id)
    if not exam:
        return None
    data = exam.model_dump(exclude={"units"})
    data["units"] = [
        u.model_dump(exclude={"questions", "transcript"}) | {"question_count": len(u.questions)}
        for u in exam.units
    ]
    return data


def exam_questions(exam_id: str) -> Optional[list[dict]]:
    """考试/练习作答用: 按 Unit 分组返回, 不含答案。"""
    exam = exam_repo.get(exam_id)
    if not exam:
        return None
    return [
        {
            "unit": u.model_dump(exclude={"questions"}),
            "questions": [_question_public(q) for q in u.questions],
        }
        for u in exam.units
    ]


def _find_question(exam: Exam, question_id: str) -> Optional[Question]:
    for unit in exam.units:
        for q in unit.questions:
            if q.id == question_id:
                return q
    return None


def submit_attempt(attempt_id: str) -> Optional[dict]:
    """判分: 以 final_answer 为准, 同时标记 is_first_correct。"""
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        return None
    exam = exam_repo.get(attempt["exam_id"])
    if not exam:
        return None

    answers = student_repo.list_answers(attempt_id)
    score = 0
    for ans in answers:
        q = _find_question(exam, ans["question_id"])
        if not q or not q.correct_answer:
            continue
        final = (ans.get("final_answer") or "").strip().upper()
        first = (ans.get("first_answer") or "").strip().upper()
        if final == q.correct_answer:
            score += 1
        is_first_correct = first == q.correct_answer if first else None
        student_repo.upsert_answer(
            attempt_id, ans["question_id"], {"is_first_correct": is_first_correct}
        )
    submitted = student_repo.submit_attempt(attempt_id, score)
    return {
        "attempt": submitted,
        "score": score,
        "question_count": exam.question_count,
    }


def list_mistakes(
    student_id: str,
    mastery: Optional[str] = None,
    tag: Optional[str] = None,
    section: Optional[str] = None,
    trained: Optional[bool] = None,
    retested: Optional[bool] = None,
) -> list[dict]:
    """错题本: 聚合每道错题的最新状态, 支持 mastery/错因/Section/训练/复测筛选。"""
    from . import review_service, training_service

    conn = student_repo._conn()
    rows = conn.execute(
        """
        SELECT a.exam_id, a.id AS attempt_id, a.submitted_at,
               aa.question_id, aa.final_answer, aa.is_first_correct,
               aa.max_hint_level, aa.relisten_count, aa.change_count, aa.dwell_ms
        FROM attempts a
        JOIN attempt_answers aa ON aa.attempt_id = a.id
        WHERE a.student_id = ? AND a.submitted_at IS NOT NULL
        ORDER BY a.submitted_at DESC
        """,
        (student_id,),
    ).fetchall()

    mistakes = []
    seen = set()
    for row in rows:
        row = dict(row)
        key = (row["exam_id"], row["question_id"])
        if key in seen:
            continue
        seen.add(key)
        exam = exam_repo.get(row["exam_id"])
        if not exam:
            continue
        q = None
        for unit in exam.units:
            for qq in unit.questions:
                if qq.id == row["question_id"]:
                    q = qq
                    break
        if not q or not q.correct_answer:
            continue
        final = (row.get("final_answer") or "").upper()
        if final == q.correct_answer:
            continue

        ans_row = {
            "is_first_correct": row["is_first_correct"],
            "relisten_count": row["relisten_count"],
        }
        q_events = review_service._question_events(
            student_repo.list_behavior_events(row["attempt_id"]), q.id
        )
        trainings = student_repo.list_training_results(student_id, q.id)
        mastery_state = training_service.question_mastery(
            ans_row, q_events, trainings
        )
        blind_retested = any(
            e["event_type"] == "blind_retest" for e in q_events
        )
        training_passed = any(
            training_service.is_training_passed(
                t.get("training_type", ""), t.get("score"), t.get("result"),
                t.get("error_details"),
            )
            for t in trainings
        )
        diagnosis = student_repo.get_diagnosis(row["attempt_id"], q.id)
        final_tags = diagnosis["final_tags"] if diagnosis else []
        student_tags = diagnosis["student_tags"] if diagnosis else []

        # 下一步(可解释规则)
        cand = review_service.question_candidates(row["attempt_id"], q.id)
        high_conf = [
            c for c in (cand or {}).get("candidates", [])
            if c["confidence"] >= training_service.CONFIDENCE_TRIGGER
        ]
        if mastery_state == "mastered":
            next_step = "已掌握, 可间隔一段时间后复测巩固"
        elif not final_tags and not high_conf and not student_tags:
            next_step = "先完成错因自判(证据不足时如实标注)"
        elif not training_passed:
            plan = training_service.training_plan(row["attempt_id"], q.id)
            types = "、".join(t["title"] for t in (plan or {}).get("trainings", []))
            next_step = f"待对症训练: {types}" if types else "待对症训练"
        elif not blind_retested:
            next_step = "待裸听复测"
        else:
            next_step = "复测未通过或复测期间使用了提示, 重新训练后再测"

        item = {
            "exam_id": row["exam_id"],
            "exam_title": exam.title,
            "attempt_id": row["attempt_id"],
            "section": q.section,
            "unit_type": [u.type for u in exam.units if u.id == q.unit_id][0],
            "question_id": q.id,
            "question_number": q.number,
            "question_text": q.question_text,
            "question_text_zh": q.question_text_zh,
            "correct_answer": q.correct_answer,
            "final_answer": row.get("final_answer"),
            "mastery": mastery_state,
            # 题目层掌握度; 错因/能力层掌握度(cause mastery)是 Phase 5 的
            # 独立维度, 禁止由 question mastery 直接映射
            "mastery_layer": "question",
            "final_tags": final_tags,
            "student_tags": student_tags,
            "training_count": len(trainings),
            "training_passed": training_passed,
            "blind_retested": blind_retested,
            "max_hint_level": row["max_hint_level"],
            "relisten_count": row["relisten_count"],
            "last_review_at": max(
                [row["submitted_at"]] + [e["server_at"] for e in q_events]
            ),
            "next_step": next_step,
        }
        # 筛选
        if mastery and mastery_state != mastery:
            continue
        if tag and tag not in final_tags and tag not in student_tags:
            continue
        if section and q.section != section:
            continue
        if trained is not None and bool(trainings) != trained:
            continue
        if retested is not None and blind_retested != retested:
            continue
        mistakes.append(item)
    return mistakes


def profile(student_id: str) -> dict:
    """简版训练指标画像: 按错因 layer 聚合作答证据, 可回链具体题。"""
    tag_dict = {k: v for k, v in _load_tags().items()}
    mistakes = list_mistakes(student_id)
    layer_stats: dict[str, dict] = {}
    for m in mistakes:
        tags = m["final_tags"] or []
        for tag in tags:
            layer = (tag_dict.get(tag) or {}).get("layer", "unknown")
            stat = layer_stats.setdefault(layer, {"count": 0, "evidence": []})
            stat["count"] += 1
            stat["evidence"].append(
                {
                    "question_id": m["question_id"],
                    "exam_id": m["exam_id"],
                    "question_number": m["question_number"],
                    "tag": tag,
                }
            )
    return {
        "student_id": student_id,
        "note": "训练指标(基于错因标签), 非标准化能力测验",
        "layers": layer_stats,
        "total_mistakes": len(mistakes),
    }


_TAGS_CACHE: Optional[dict] = None


def _load_tags() -> dict:
    global _TAGS_CACHE
    if _TAGS_CACHE is None:
        from .repository import load_tag_dictionary

        _TAGS_CACHE = load_tag_dictionary()
    return _TAGS_CACHE
