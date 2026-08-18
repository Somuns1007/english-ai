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


def list_mistakes(student_id: str) -> list[dict]:
    """错题本: 所有提交了但答错的题(final 错或首答错)。"""
    conn = student_repo._conn()
    rows = conn.execute(
        """
        SELECT a.exam_id, a.id AS attempt_id, a.submitted_at,
               aa.question_id, aa.final_answer, aa.is_first_correct,
               aa.max_hint_level, aa.relisten_count
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
        exam = exam_repo.get(row["exam_id"])
        if not exam:
            continue
        q = _find_question(exam, row["question_id"])
        if not q or not q.correct_answer:
            continue
        final = (row.get("final_answer") or "").upper()
        if final == q.correct_answer:
            continue
        key = (row["exam_id"], row["question_id"])
        if key in seen:
            continue
        seen.add(key)
        diagnosis = student_repo.get_diagnosis(row["attempt_id"], row["question_id"])
        mistakes.append(
            {
                "exam_id": row["exam_id"],
                "exam_title": exam.title,
                "section": q.section,
                "question_id": q.id,
                "question_number": q.number,
                "question_text": q.question_text,
                "question_text_zh": q.question_text_zh,
                "correct_answer": q.correct_answer,
                "final_answer": row.get("final_answer"),
                "is_first_correct": bool(row["is_first_correct"])
                if row["is_first_correct"] is not None
                else None,
                "max_hint_level": row["max_hint_level"],
                "relisten_count": row["relisten_count"],
                "submitted_at": row["submitted_at"],
                "final_tags": diagnosis["final_tags"] if diagnosis else [],
                "attempt_id": row["attempt_id"],
            }
        )
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
