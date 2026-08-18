# -*- coding: utf-8 -*-
"""听力模块 API 路由。所有端点挂载在 /api/listening 前缀下。"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from . import service
from .models import AnswerUpsert, AttemptCreate, DiagnosisIn, TrainingResultIn
from .repository import exam_repo, load_tag_dictionary, student_repo

router = APIRouter(prefix="/api/listening", tags=["listening"])


@router.get("/exams")
def list_exams(student_id: str = Query("anonymous")):
    return {"data": [s.model_dump() for s in service.exam_summaries(student_id)]}


@router.get("/exams/{exam_id}")
def get_exam(exam_id: str):
    data = service.exam_detail(exam_id)
    if not data:
        raise HTTPException(status_code=404, detail="套题不存在")
    return {"data": data}


@router.get("/exams/{exam_id}/questions")
def get_exam_questions(exam_id: str):
    """作答用题目(不含答案/解析)。"""
    data = service.exam_questions(exam_id)
    if data is None:
        raise HTTPException(status_code=404, detail="套题不存在")
    return {"data": data}


@router.get("/audio/{exam_id}")
def get_audio(exam_id: str):
    path = exam_repo.audio_file(exam_id)
    if not path:
        raise HTTPException(status_code=404, detail="音频不存在")
    media_type = "audio/mp4" if path.suffix == ".m4a" else "audio/mpeg"
    return FileResponse(path, media_type=media_type)


@router.get("/tag-dictionary")
def get_tag_dictionary():
    return {"data": load_tag_dictionary()}


@router.post("/attempts")
def create_attempt(body: AttemptCreate):
    if not exam_repo.get(body.exam_id):
        raise HTTPException(status_code=404, detail="套题不存在")
    attempt = student_repo.create_attempt(body.student_id, body.exam_id, body.mode)
    return {"data": attempt}


@router.put("/attempts/{attempt_id}/answers/{question_id}")
def upsert_answer(attempt_id: str, question_id: str, body: AnswerUpsert):
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if attempt["submitted_at"]:
        raise HTTPException(status_code=409, detail="该次作答已提交, 不可修改")
    fields = body.model_dump(exclude_none=True)
    student_repo.upsert_answer(attempt_id, question_id, fields)
    return {"data": {"ok": True}}


@router.post("/attempts/{attempt_id}/submit")
def submit_attempt(attempt_id: str):
    result = service.submit_attempt(attempt_id)
    if not result:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    return {"data": result}


@router.get("/attempts/{attempt_id}/review")
def review_attempt(attempt_id: str):
    """提交后才能复盘: 未提交不泄露答案。"""
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if not attempt["submitted_at"]:
        raise HTTPException(status_code=409, detail="提交后才能查看复盘")
    return {"data": service.review_view(attempt_id)}


@router.post("/diagnoses")
def save_diagnosis(body: DiagnosisIn):
    attempt = student_repo.get_attempt(body.attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    exam = exam_repo.get(attempt["exam_id"])
    ai_tags: list[dict] = []
    if exam:
        for unit in exam.units:
            for q in unit.questions:
                if q.id == body.question_id:
                    ai_tags = q.ai_annotation.diagnosis_candidates
    result = student_repo.upsert_diagnosis(
        body.student_id,
        body.attempt_id,
        body.question_id,
        body.student_tags,
        ai_tags,
        body.final_tags,
    )
    return {"data": result}


@router.post("/training-results")
def save_training_result(body: TrainingResultIn):
    result = student_repo.add_training_result(
        body.student_id,
        body.question_id,
        body.training_type,
        body.pre_result,
        body.post_result,
    )
    return {"data": result}


@router.get("/mistakes")
def list_mistakes(student_id: str = Query("anonymous")):
    return {"data": service.list_mistakes(student_id)}


@router.get("/profile")
def get_profile(student_id: str = Query("anonymous")):
    return {"data": service.profile(student_id)}
