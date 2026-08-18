# -*- coding: utf-8 -*-
"""听力模块 API 路由。所有端点挂载在 /api/listening 前缀下。"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from . import review_service, service
from .models import (
    AnswerUpsert,
    AttemptCreate,
    BehaviorEventBatch,
    DiagnosisIn,
    HintRequest,
    RetryIn,
    TrainingResultIn,
)
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


@router.get("/attempts/in-progress")
def find_in_progress(
    exam_id: str = Query(...),
    mode: str = Query("practice_mode"),
    student_id: str = Query("anonymous"),
):
    """刷新恢复: 查找未提交 attempt 并带回已保存答案。"""
    attempt = student_repo.find_in_progress_attempt(student_id, exam_id, mode)
    if not attempt:
        return {"data": None}
    return {"data": {"attempt": attempt, "answers": student_repo.list_answers(attempt["id"])}}


@router.post("/attempts/{attempt_id}/events")
def post_behavior_events(attempt_id: str, body: BehaviorEventBatch):
    """行为事件批量上报。只记录, 不据此自动判定学生错因。"""
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    saved = student_repo.add_behavior_events(body.student_id, attempt_id, body.events)
    return {"data": {"saved": saved}}


@router.get("/attempts/{attempt_id}/events")
def list_behavior_events(attempt_id: str, event_type: str = Query(None)):
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    return {"data": student_repo.list_behavior_events(attempt_id, event_type)}


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
    """复盘总览(门控): 提交后可用; 正确答案仅在解锁 L5 后随题目返回。"""
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    if not attempt["submitted_at"]:
        raise HTTPException(status_code=409, detail="提交后才能查看复盘")
    data = review_service.review_overview(attempt_id)
    if not data:
        raise HTTPException(status_code=404, detail="套题不存在")
    return {"data": data}


@router.post("/attempts/{attempt_id}/questions/{question_id}/hint")
def open_hint(attempt_id: str, question_id: str, body: HintRequest):
    """打开某级提示。逐级解锁, 服务端强制; 每次解锁记录 hint_open(level)。"""
    result = review_service.unlock_hint(
        attempt_id, question_id, body.level, body.teacher_mode
    )
    if result is None:
        raise HTTPException(status_code=404, detail="作答或题目不存在, 或尚未提交")
    if result.get("error") == "locked":
        raise HTTPException(status_code=409, detail=result["message"])
    return {"data": result}


@router.post("/attempts/{attempt_id}/questions/{question_id}/retry")
def retry_question(attempt_id: str, question_id: str, body: RetryIn):
    """错题重答: 只返回对错, 不泄露正确答案。"""
    result = review_service.retry_answer(attempt_id, question_id, body.answer)
    if result is None:
        raise HTTPException(status_code=404, detail="作答或题目不存在, 或尚未提交")
    return {"data": result}


@router.get("/attempts/{attempt_id}/questions/{question_id}/candidates")
def get_candidates(attempt_id: str, question_id: str):
    """系统候选错因(基于行为证据, 仅供参考, 不写入 final_tags)。"""
    result = review_service.question_candidates(attempt_id, question_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作答或题目不存在")
    return {"data": result}


@router.get("/self-diagnosis-options")
def get_self_diagnosis_options():
    import json as _json
    from .repository import DATA_DIR

    path = DATA_DIR / "self_diagnosis_options.json"
    if not path.exists():
        return {"data": []}
    return {"data": _json.loads(path.read_text(encoding="utf-8"))}


@router.post("/diagnoses")
def save_diagnosis(body: DiagnosisIn):
    attempt = student_repo.get_attempt(body.attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    # ai_tags 不再从题目层 ai_annotation 复制:
    # 系统推测以 /candidates 接口的行为证据版为准, 诊断记录只保存
    # 学生自判(student_tags)与最终确认(final_tags), 保持分层。
    result = student_repo.upsert_diagnosis(
        body.student_id,
        body.attempt_id,
        body.question_id,
        body.student_tags,
        [],
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
