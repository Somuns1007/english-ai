# -*- coding: utf-8 -*-
"""听力模块 API 路由。所有端点挂载在 /api/listening 前缀下。"""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import (
    v2_exam_service,
    v2_practice_service,
    aural_lexicon_service,
    stem_bank_service,
    dashboard_service,
    corpus_service,
    expression_service,
    profile_service,
    review_service,
    service,
    training_service,
)
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


def require_teacher(
    x_teacher_token: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
):
    """教师接口最小鉴权: 密钥只在服务端环境变量, 不进前端代码。

    前端教师页要求用户每次会话输入口令(sessionStorage 保存, 随页面关闭清除),
    经 X-Teacher-Token 头发送; <audio> 标签无法带头, 音频接口允许 query token 兜底。
    服务端未配置 TEACHER_TOKEN 时教师接口整体禁用。
    """
    expected = os.getenv("TEACHER_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="教师接口未启用(服务端未配置 TEACHER_TOKEN)")
    provided = x_teacher_token or token
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="教师口令无效或未提供")


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
    if v2_exam_service.is_v2_exam(body.exam_id) and not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该套题尚未发布")
    if not exam_repo.get(body.exam_id) and not v2_exam_service.is_v2_exam(body.exam_id):
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
    attempt = student_repo.get_attempt(attempt_id)
    if attempt and v2_exam_service.is_v2_exam(attempt["exam_id"]):
        result = service.submit_v2_attempt(attempt_id)
    else:
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
    """训练结果落库。证据链字段由服务端权威判定, 不信任客户端上报:
    - diagnosis_id/diagnosis_revision: 绑定"当前有效诊断"(而非客户端传的旧值)
    - provenance: 由题目数据判定(teacher_calibrated / generated_unverified)
    - trigger_tags: 快照当前训练计划中触发了该训练类型的错因
    """
    diagnosis_id = body.diagnosis_id
    diagnosis_revision = None
    provenance = None
    trigger_tags: list[str] = []
    if body.attempt_id:
        attempt = student_repo.get_attempt(body.attempt_id)
        exam = exam_repo.get(attempt["exam_id"]) if attempt else None
        q = training_service._find_question(exam, body.question_id) if exam else None
        if q is not None:
            diag = student_repo.get_diagnosis(body.attempt_id, body.question_id)
            if diag:
                diagnosis_id = diag["id"]
                diagnosis_revision = diag["revision"]
            provenance = training_service.training_provenance(q, body.training_type)
            plan = training_service.training_plan(body.attempt_id, body.question_id)
            if plan and plan.get("available"):
                trigger_tags = sorted({
                    t["triggered_by"]
                    for t in plan["trainings"]
                    if t["type"] == body.training_type
                })
    result = student_repo.add_training_result(
        body.student_id,
        body.question_id,
        body.training_type,
        body.pre_result,
        body.post_result,
        attempt_id=body.attempt_id,
        diagnosis_id=diagnosis_id,
        diagnosis_revision=diagnosis_revision,
        provenance=provenance,
        trigger_tags=trigger_tags,
        input=body.input,
        result=body.result,
        score=body.score,
        error_details=body.error_details,
        hints_used=body.hints_used,
        duration_ms=body.duration_ms,
    )
    return {"data": result}


@router.get("/mistakes")
def list_mistakes(
    student_id: str = Query("anonymous"),
    mastery: str = Query(None),
    tag: str = Query(None),
    section: str = Query(None),
    trained: bool = Query(None),
    retested: bool = Query(None),
):
    return {
        "data": service.list_mistakes(
            student_id, mastery=mastery, tag=tag,
            section=section, trained=trained, retested=retested,
        )
    }


# ---------- Phase 4: 对症训练 ----------


@router.get("/attempts/{attempt_id}/questions/{question_id}/training-plan")
def get_training_plan(attempt_id: str, question_id: str):
    """错因驱动的训练推荐; 证据不足时不出训练。"""
    plan = training_service.training_plan(attempt_id, question_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="作答或题目不存在, 或尚未提交")
    return {"data": plan}


_TRAINING_BUILDERS = {
    "dictation": training_service.dictation_content,
    "chunk": training_service.chunk_content,
    "paraphrase": training_service.paraphrase_content,
    "distractor": training_service.distractor_content,
}


def _load_question_for_training(attempt_id: str, question_id: str):
    attempt = student_repo.get_attempt(attempt_id)
    if not attempt or not attempt["submitted_at"]:
        return None, None
    exam = exam_repo.get(attempt["exam_id"])
    q = review_service._find_question(exam, question_id) if exam else None
    return attempt, q


@router.get("/attempts/{attempt_id}/questions/{question_id}/training/{training_type}")
def get_training_content(attempt_id: str, question_id: str, training_type: str):
    attempt, q = _load_question_for_training(attempt_id, question_id)
    builder = _TRAINING_BUILDERS.get(training_type)
    if not attempt or not q:
        raise HTTPException(status_code=404, detail="作答或题目不存在, 或尚未提交")
    if not builder:
        raise HTTPException(status_code=404, detail="未知训练类型")
    content = builder(q)
    if content is None:
        return {
            "data": None,
            "message": "该题暂无此训练所需的内容(定位句或教师标注待补充, needs_review)。",
        }
    return {"data": content}


class _CheckBody(BaseModel):
    level: Optional[int] = None
    inputs: list[str] = []
    order: list[int] = []
    answers_map: dict[str, str] = {}
    selections: dict[str, list[str]] = {}


@router.post("/attempts/{attempt_id}/questions/{question_id}/training/{training_type}/check")
def check_training(attempt_id: str, question_id: str, training_type: str, body: _CheckBody):
    """服务端判分: 返回 score/result/错误位置明细; 答案只在判分时返回。"""
    attempt, q = _load_question_for_training(attempt_id, question_id)
    if not attempt or not q:
        raise HTTPException(status_code=404, detail="作答或题目不存在, 或尚未提交")
    if training_type == "dictation":
        result = training_service.dictation_check(q, body.level or 3, body.inputs)
    elif training_type == "chunk":
        result = training_service.chunk_check(q, body.order)
    elif training_type == "paraphrase":
        result = training_service.paraphrase_check(q, body.answers_map)
    elif training_type == "distractor":
        result = training_service.distractor_check(q, body.selections)
    else:
        raise HTTPException(status_code=404, detail="未知训练类型")
    if result is None:
        raise HTTPException(status_code=404, detail="该题暂无此训练内容(needs_review)")
    return {"data": result}


@router.post("/attempts/{attempt_id}/questions/{question_id}/blind-retest")
def blind_retest(attempt_id: str, question_id: str, body: RetryIn):
    """裸听复测: 无提示环境下重答; 只返回对错。是 improved→mastered 的核心证据。"""
    result = training_service.blind_retest(attempt_id, question_id, body.answer)
    if result is None:
        raise HTTPException(status_code=404, detail="作答或题目不存在, 或尚未提交")
    return {"data": result}


@router.get("/profile")
def get_profile(student_id: str = Query("anonymous")):
    """Phase 5A 证据画像: cause 聚合 → confidence/current_risk/cause_mastery
    → skill 聚合 → trend → 规则化推荐。全部规则计算, 可反查 evidence_refs。"""
    return {"data": profile_service.build_profile(student_id)}


@router.get("/profile/causes")
def get_profile_causes(student_id: str = Query("anonymous")):
    return {"data": profile_service.build_cause_profile(student_id)}


@router.get("/profile/skills")
def get_profile_skills(student_id: str = Query("anonymous")):
    causes = profile_service.build_cause_profile(student_id)
    return {"data": profile_service.build_skill_profile(causes)}


# ---------- Phase 6: Expression Bridge 跨语境训练 ----------


class ExpressionSubmitIn(BaseModel):
    student_id: str
    answers: dict[str, str] = {}
    listen_count_before_submit: int = 0
    reveal_used: bool = False  # 提交前放弃盲听直接看文本(重要行为信号)
    duration_ms: Optional[int] = None


@router.get("/expressions")
def list_expressions(student_id: str = Query("anonymous")):
    """表达卡片列表(含该学生进度)。表达全部 source_type=official_exam, 可追溯。"""
    return {"data": expression_service.list_expressions(student_id)}


@router.get("/expressions/scenarios/{scenario_id}/audio")
def get_scenario_audio(scenario_id: str):
    """AI 场景 TTS 音频。元信息里 source_type=ai_generated_tts, 不冒充真实语料。"""
    path = expression_service.scenario_audio_path(scenario_id)
    if not path:
        raise HTTPException(status_code=404, detail="音频不存在")
    meta = expression_service.scenario_audio_meta(scenario_id) or {}
    return FileResponse(
        path,
        media_type="audio/mpeg",
        headers={
            "X-Audio-Source-Type": meta.get("source_type", "ai_generated_tts"),
            "X-Audio-Voice": meta.get("voice_id", ""),
        },
    )


@router.get("/expressions/scenarios/{scenario_id}/audio-meta")
def get_scenario_audio_meta(scenario_id: str):
    meta = expression_service.scenario_audio_meta(scenario_id)
    if not meta:
        raise HTTPException(status_code=404, detail="音频记录不存在")
    return {"data": meta}


@router.get("/expressions/{expression_id}")
def get_expression(expression_id: str, student_id: str = Query("anonymous")):
    """表达详情 + 场景列表。场景不含 text 与答案(先听不看文本)。"""
    data = expression_service.expression_detail(expression_id, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="表达不存在")
    return {"data": data}


@router.post("/expressions/scenarios/{scenario_id}/reveal-early")
def reveal_scenario_early(scenario_id: str):
    """放弃盲听, 提前揭示文本(不含答案)。reveal_used 在提交时随行为数据落库。"""
    result = expression_service.early_reveal(scenario_id)
    if result is None:
        raise HTTPException(status_code=404, detail="场景不存在")
    return {"data": result}


@router.post("/expressions/scenarios/{scenario_id}/submit")
def submit_scenario(scenario_id: str, body: ExpressionSubmitIn):
    """提交三题作答: 服务端判分, 落 expression_attempts 证据表, 返回揭示内容。"""
    result = expression_service.submit_scenario(
        scenario_id,
        body.student_id,
        body.answers,
        body.listen_count_before_submit,
        body.reveal_used,
        body.duration_ms,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="场景不存在")
    return {"data": result}


@router.post("/expression-attempts/{attempt_id}/replayed")
def expression_replay_after_reveal(attempt_id: str):
    """揭示文本后再次播放音频的计数。"""
    if not expression_service.record_replay_after_reveal(attempt_id):
        raise HTTPException(status_code=404, detail="训练记录不存在")
    return {"data": {"ok": True}}


# ---------- Phase 6.1: 教师审核(最小可用版, 本地单机无鉴权) ----------


class TeacherExpressionUpdate(BaseModel):
    meaning: Optional[str] = None
    communicative_function: Optional[str] = None
    related_expressions: Optional[list[str]] = None


class TeacherScenarioUpdate(BaseModel):
    text: Optional[str] = None
    scenario: Optional[str] = None
    communicative_function: Optional[str] = None
    difficulty: Optional[str] = None
    target_surface: Optional[str] = None


class TeacherReviewAction(BaseModel):
    action: str  # approve / reject


@router.get("/teacher/expressions", dependencies=[Depends(require_teacher)])
def teacher_list_expressions():
    """教师审核列表(含场景审核状态)。"""
    return {"data": expression_service.teacher_expression_overview()}


@router.get("/teacher/expressions/{expression_id}", dependencies=[Depends(require_teacher)])
def teacher_expression_detail(expression_id: str):
    """教师视图: 完整场景文本与答案, 供审核。"""
    data = expression_service.teacher_expression_detail(expression_id)
    if not data:
        raise HTTPException(status_code=404, detail="表达不存在")
    return {"data": data}


@router.put("/teacher/expressions/{expression_id}", dependencies=[Depends(require_teacher)])
def teacher_update_expression(expression_id: str, body: TeacherExpressionUpdate):
    result = expression_service.update_expression(
        expression_id, body.model_dump(exclude_none=True)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="表达不存在")
    if result.get("error") == "no_fields":
        raise HTTPException(status_code=400, detail="没有可更新的字段")
    return {"data": result}


@router.put("/teacher/scenarios/{scenario_id}", dependencies=[Depends(require_teacher)])
def teacher_update_scenario(scenario_id: str, body: TeacherScenarioUpdate):
    """编辑场景文本。text 变更会作废旧 TTS 音频, 需重新生成。"""
    result = expression_service.update_scenario(
        scenario_id, body.model_dump(exclude_none=True)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="场景不存在")
    if result.get("error") == "no_fields":
        raise HTTPException(status_code=400, detail="没有可更新的字段")
    if result.get("error") == "target_missing":
        raise HTTPException(status_code=400, detail=result["message"])
    return {"data": result}


@router.post("/teacher/expressions/{expression_id}/review", dependencies=[Depends(require_teacher)])
def teacher_review_expression(expression_id: str, body: TeacherReviewAction):
    result = expression_service.review_expression(expression_id, body.action)
    if result is None:
        raise HTTPException(status_code=404, detail="表达不存在")
    if result.get("error"):
        raise HTTPException(status_code=400, detail="action 必须是 approve 或 reject")
    return {"data": result}


@router.post("/teacher/scenarios/{scenario_id}/review", dependencies=[Depends(require_teacher)])
def teacher_review_scenario(scenario_id: str, body: TeacherReviewAction):
    result = expression_service.review_scenario(scenario_id, body.action)
    if result is None:
        raise HTTPException(status_code=404, detail="场景不存在")
    if result.get("error"):
        raise HTTPException(status_code=400, detail="action 必须是 approve 或 reject")
    return {"data": result}


class RegenerateAudioIn(BaseModel):
    voice: Optional[str] = None


@router.post("/teacher/scenarios/{scenario_id}/regenerate-audio", dependencies=[Depends(require_teacher)])
def teacher_regenerate_audio(scenario_id: str, body: RegenerateAudioIn):
    """重新生成场景 TTS(文本变更后必需)。仍标注 ai_generated_tts。"""
    meta = expression_service.regenerate_scenario_audio(scenario_id, body.voice)
    if meta is None:
        raise HTTPException(status_code=404, detail="场景不存在")
    return {"data": meta}


# ---------- Phase 7: 真实语料 ingestion(全部教师鉴权) ----------


@router.post("/teacher/corpus/assets", dependencies=[Depends(require_teacher)])
async def corpus_upload_asset(
    file: UploadFile,
    title: str = Query(...),
    source_name: str = Query(""),
    source_url: str = Query(None),
    license_: str = Query("", alias="license"),
    permission_status: str = Query("unverified"),
    consent_id: str = Query(None),
    speaker_ids: str = Query(None),
    commercial_permission: bool = Query(False),
    editing_permission: bool = Query(False),
    ai_processing_permission: bool = Query(False),
    recorded_at: str = Query(None),
):
    """上传长音频 + 来源/许可元数据。许可不明可上传但不可批准。

    自建录音(permission_status=owned)建议随传授权链字段;
    缺少 consent_id 的 owned 素材无法被批准、不进学生端。
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    consent = {
        "consent_id": consent_id,
        "speaker_ids": [s for s in (speaker_ids or "").split(",") if s],
        "commercial_permission": commercial_permission,
        "editing_permission": editing_permission,
        "ai_processing_permission": ai_processing_permission,
        "recorded_at": recorded_at,
    }
    asset = corpus_service.create_asset(
        content, file.filename or "audio.bin", title,
        source_name, source_url, license_, permission_status,
        consent=consent,
    )
    return {"data": asset}


@router.get("/teacher/corpus/assets", dependencies=[Depends(require_teacher)])
def corpus_list_assets():
    return {"data": student_repo.list_corpus_assets()}


@router.get("/teacher/corpus/assets/{asset_id}", dependencies=[Depends(require_teacher)])
def corpus_asset_detail(asset_id: str):
    asset = student_repo.get_corpus_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    return {"data": {**asset, "clips": student_repo.list_corpus_clips(asset_id)}}


@router.get("/teacher/corpus/assets/{asset_id}/audio", dependencies=[Depends(require_teacher)])
def corpus_asset_audio(asset_id: str):
    path = corpus_service.asset_audio_path(asset_id)
    if not path:
        raise HTTPException(status_code=404, detail="音频不存在")
    media = "audio/wav" if path.suffix == ".wav" else "audio/mpeg"
    return FileResponse(path, media_type=media)


class _AssetMetaUpdate(BaseModel):
    title: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None
    permission_status: Optional[str] = None
    consent_id: Optional[str] = None
    speaker_ids: Optional[list[str]] = None
    commercial_permission: Optional[bool] = None
    editing_permission: Optional[bool] = None
    ai_processing_permission: Optional[bool] = None
    recorded_at: Optional[str] = None


@router.put("/teacher/corpus/assets/{asset_id}", dependencies=[Depends(require_teacher)])
def corpus_update_asset(asset_id: str, body: _AssetMetaUpdate):
    result = corpus_service.update_asset_metadata(
        asset_id, body.model_dump(exclude_none=True)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    if result.get("error") == "no_fields":
        raise HTTPException(status_code=400, detail="没有可更新的字段")
    return {"data": result}


class _ReviewAction(BaseModel):
    action: str


@router.post("/teacher/corpus/assets/{asset_id}/review", dependencies=[Depends(require_teacher)])
def corpus_review_asset(asset_id: str, body: _ReviewAction):
    result = corpus_service.review_asset(asset_id, body.action)
    if result is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    if result.get("error") == "bad_action":
        raise HTTPException(status_code=400, detail="action 必须是 approve 或 reject")
    if result.get("error") == "permission":
        raise HTTPException(status_code=409, detail=result["message"])
    return {"data": result}


@router.post("/teacher/corpus/assets/{asset_id}/run-asr", dependencies=[Depends(require_teacher)])
def corpus_run_asr(asset_id: str):
    result = corpus_service.run_asr(asset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    if result.get("error"):
        raise HTTPException(status_code=409, detail=result["error"])
    return {"data": result}


@router.post("/teacher/corpus/assets/{asset_id}/run-segmentation", dependencies=[Depends(require_teacher)])
def corpus_run_segmentation(asset_id: str):
    result = corpus_service.run_segmentation(asset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    if result.get("error"):
        raise HTTPException(status_code=409, detail=result["error"])
    return {"data": result}


@router.post("/teacher/corpus/assets/{asset_id}/run-matching", dependencies=[Depends(require_teacher)])
def corpus_run_matching(asset_id: str):
    result = corpus_service.run_matching(asset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    if result.get("error"):
        raise HTTPException(status_code=409, detail=result["error"])
    return {"data": result}


class _ClipUpdate(BaseModel):
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    transcript: Optional[str] = None
    scenario_tags: Optional[list[str]] = None
    communicative_function: Optional[str] = None
    difficulty: Optional[str] = None
    speaker_info: Optional[str] = None
    accent: Optional[str] = None
    speaker_count: Optional[int] = None
    speech_rate: Optional[str] = None
    listening_features: Optional[list[str]] = None


@router.put("/teacher/corpus/clips/{clip_id}", dependencies=[Depends(require_teacher)])
def corpus_update_clip(clip_id: str, body: _ClipUpdate):
    result = corpus_service.update_clip(clip_id, body.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=404, detail="clip 不存在")
    if result.get("error") == "no_fields":
        raise HTTPException(status_code=400, detail="没有可更新的字段")
    if result.get("error") == "bad_range":
        raise HTTPException(status_code=400, detail=result["message"])
    return {"data": result}


@router.post("/teacher/corpus/clips/{clip_id}/review", dependencies=[Depends(require_teacher)])
def corpus_review_clip(clip_id: str, body: _ReviewAction):
    result = corpus_service.review_clip(clip_id, body.action)
    if result is None:
        raise HTTPException(status_code=404, detail="clip 不存在")
    if result.get("error") == "bad_action":
        raise HTTPException(status_code=400, detail="action 必须是 approve 或 reject")
    if result.get("error") == "permission":
        raise HTTPException(status_code=409, detail=result["message"])
    return {"data": result}


# ---------- Phase 7.6: 手工 clip / 匹配确认 / 学生端语料 ----------

class _ClipCreate(BaseModel):
    start_ms: int
    end_ms: int
    transcript: Optional[str] = None
    speaker_info: Optional[str] = None


@router.post("/teacher/corpus/assets/{asset_id}/clips", dependencies=[Depends(require_teacher)])
def corpus_create_clip(asset_id: str, body: _ClipCreate):
    result = corpus_service.create_clip(
        asset_id, body.start_ms, body.end_ms, body.transcript, body.speaker_info
    )
    if result is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    if result.get("error") == "bad_range":
        raise HTTPException(status_code=400, detail=result["message"])
    return {"data": result}


class _MatchReview(BaseModel):
    expression_id: str
    action: str  # approve / reject / add
    matched_text: Optional[str] = None
    match_type: Optional[str] = None
    note: Optional[str] = None


@router.post("/teacher/corpus/clips/{clip_id}/matches", dependencies=[Depends(require_teacher)])
def corpus_review_clip_match(clip_id: str, body: _MatchReview):
    if body.action == "add":
        # 教师手动建立关联(含 communicative_equivalent), 直接 approved
        if not body.matched_text or not body.match_type:
            raise HTTPException(status_code=400,
                                detail="add 需要 matched_text 和 match_type")
        result = corpus_service.add_clip_match(
            clip_id, body.expression_id, body.matched_text,
            body.match_type, body.note or "")
        if result is None:
            raise HTTPException(status_code=404, detail="clip 不存在")
        if result.get("error") in ("bad_match_type", "no_expression"):
            raise HTTPException(status_code=400, detail=result["message"])
        if result.get("error") == "duplicate":
            raise HTTPException(status_code=409, detail=result["message"])
        return {"data": result}
    result = corpus_service.review_clip_match(clip_id, body.expression_id, body.action)
    if result is None:
        raise HTTPException(status_code=404, detail="clip 不存在")
    if result.get("error") == "bad_action":
        raise HTTPException(status_code=400, detail="action 必须是 approve / reject / add")
    if result.get("error") == "no_candidate":
        raise HTTPException(status_code=409, detail=result["message"])
    return {"data": result}


@router.get("/corpus/clips")
def corpus_student_clips():
    """学生端: 仅返回已批准且有许可的 authentic clips, 带 attribution。"""
    return {"data": corpus_service.list_approved_clips()}


@router.get("/corpus/clips/{clip_id}/audio")
def corpus_student_clip_audio(clip_id: str):
    """学生端音频: 服务端按 clip 区间精确切片, 学生拿不到未批准区间。"""
    data = corpus_service.clip_audio_slice(clip_id)
    if data is None:
        raise HTTPException(status_code=404, detail="clip 不存在或未批准")
    from fastapi.responses import Response

    return Response(content=data, media_type="audio/wav")

# ================= V2.1 Exam Mode(白名单 DTO, audio_only) =================


@router.get("/v2/exams")
def v2_list_exams():
    """V2 套题列表: 只含元信息, 不含题目内容。"""
    return {"data": v2_exam_service.exam_summaries()}


@router.get("/v2/exams/{exam_id}/paper")
def v2_exam_paper(exam_id: str):
    """作答卷面: 白名单 DTO(题号+英文选项), 服务端递归断言无禁止字段。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该套题尚未发布")
    dto = v2_exam_service.paper_dto(exam_id)
    if dto is None:
        raise HTTPException(status_code=404, detail="V2 套题不存在")
    return {"data": dto}


@router.get("/v2/exams/{exam_id}/audio")
def v2_exam_audio(exam_id: str):
    """整套原始音频(无 unit 切分, 无题号映射)。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该套题尚未发布")
    path = v2_exam_service.audio_file(exam_id)
    if not path:
        raise HTTPException(status_code=404, detail="音频不存在")
    media_type = "audio/mp4" if path.suffix == ".m4a" else "audio/mpeg"
    return FileResponse(path, media_type=media_type)
# ================= V2.2 Continuous Practice(Pilot) =================
# 教学语义:
#   - round2 答对 = recovered_after_full_replay, 不是"第二遍理解率"
#   - 任何端点都不返回逐题对错/正确答案; 只返回数量
#   - release gate 与 V2.1 共用; profile_eligible=False


@router.get("/v2/practice/materials")
def v2_practice_materials():
    """Pilot 材料列表: 只含元信息。"""
    return {"data": v2_practice_service.material_summaries()}


@router.get("/v2/practice/materials/{material_id}")
def v2_practice_bundle(material_id: str):
    """练习 bundle: 白名单 DTO(题干+英文选项+音频区间), 递归断言无禁止字段。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    dto = v2_practice_service.material_bundle(material_id)
    if dto is None:
        raise HTTPException(status_code=404, detail="材料不存在")
    return {"data": dto}


@router.get("/v2/practice/materials/{material_id}/audio")
def v2_practice_audio(material_id: str):
    """整套原始音频; material 区间由前端钳制播放(工程 Pilot)。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    path = v2_practice_service.audio_file(material_id)
    if not path:
        raise HTTPException(status_code=404, detail="音频不存在")
    media_type = "audio/mp4" if path.suffix == ".m4a" else "audio/mpeg"
    return FileResponse(path, media_type=media_type)


class _CpSessionCreate(BaseModel):
    student_id: str = "anonymous"
    material_id: str


class _CpEventIn(BaseModel):
    event_type: str
    payload: dict = {}
    client_at: Optional[str] = None


class _CpEventBatch(BaseModel):
    student_id: str = "anonymous"
    events: list[_CpEventIn]


class _CpAnswers(BaseModel):
    answers: dict[str, str]


@router.post("/v2/practice/sessions")
def v2_practice_create_session(body: _CpSessionCreate):
    """创建 session: pin 内容 revision/hash + round2 选项顺序。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    session = v2_practice_service.create_session(body.student_id, body.material_id)
    if session is None:
        raise HTTPException(status_code=404, detail="材料不存在")
    return {"data": {"session_id": session["id"], "stage": session["stage"]}}


@router.get("/v2/practice/sessions/find")
def v2_practice_find_session(
    material_id: str = Query(...), student_id: str = Query("anonymous"),
):
    """刷新恢复: 找该学生在该材料上最近的 session。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    session = v2_practice_service.find_session(student_id, material_id)
    if not session:
        return {"data": None}
    return {"data": {"session_id": session["id"]}}


@router.get("/v2/practice/sessions/{session_id}")
def v2_practice_session_state(session_id: str):
    """按阶段返回恢复状态(白名单; 无答案/无逐题对错)。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    state = v2_practice_service.session_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session 不存在")
    return {"data": state}


@router.post("/v2/practice/sessions/{session_id}/events")
def v2_practice_events(session_id: str, body: _CpEventBatch):
    """行为事件批量上报(白名单事件类型; 只记录事实)。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    try:
        result = v2_practice_service.record_events(
            session_id, body.student_id, [e.model_dump() for e in body.events])
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="session 不存在")
    return {"data": result}


@router.post("/v2/practice/sessions/{session_id}/round1")
def v2_practice_round1(session_id: str, body: _CpAnswers):
    """round 1 提交: 需有效 first pass; 只返回数量, 不返回逐题对错。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    result = v2_practice_service.submit_round1(session_id, body.answers)
    if result is None:
        raise HTTPException(status_code=404, detail="session 不存在")
    if result.get("error"):
        raise HTTPException(status_code=409, detail=result["error"])
    return {"data": result}


@router.post("/v2/practice/sessions/{session_id}/round2")
def v2_practice_round2(session_id: str, body: _CpAnswers):
    """recovery 提交: 需有效 blind replay; 答对记 recovered_after_full_replay。"""
    if not v2_exam_service.gate_allows():
        raise HTTPException(status_code=403, detail="该练习尚未发布")
    result = v2_practice_service.submit_round2(session_id, body.answers)
    if result is None:
        raise HTTPException(status_code=404, detail="session 不存在")
    if result.get("error"):
        raise HTTPException(status_code=409, detail=result["error"])
    return {"data": result}


# ── Aural Lexicon 端点 (V2.C CET Track) ──────────────────────────────────────
# 所有端点：
#   - DTO 白名单：只返回 lexical 字段，禁止 transcript/答案/标注理由
#   - attempt 只写 lexical_item_recognized，禁止 ability 结论字段
#   - Phase 0 active 期间不开六级单元练习/全真/probe（由 phase0_active 字段控制前端路由）


class _LexAttemptIn(BaseModel):
    student_id: str
    item_id: str
    task_type: str          # hear_identify | micro_dictation | speed_ladder
    is_correct: bool
    response: Optional[str] = None
    response_latency_ms: Optional[int] = None


class _EntryTestResultsIn(BaseModel):
    student_id: str
    results: list[dict]     # [{"item_id": str, "is_correct": bool}]
    threshold: float = 0.70


class _Phase0CompleteIn(BaseModel):
    student_id: str
    retest_score: float


class _HarvestIn(BaseModel):
    student_id: str
    item_id: str
    gate_type: str   # 'exam_attempt' | 'cp_session'
    gate_id: str     # attempt_id 或 session_id


class _SeedIn(BaseModel):
    pass  # admin-only, no body needed


@router.post("/lexicon/seed")
def lexicon_seed():
    """将 lexicon_v1.json 词条载入数据库（幂等）。仅内部/开发用。"""
    result = aural_lexicon_service.seed_lexicon()
    return {"data": result}


@router.get("/lexicon/session")
def lexicon_daily_session(student_id: str = Query(...)):
    """今日词汇会话：到期复习 + 新词引入。Phase 0 期间配额加重。"""
    return {"data": aural_lexicon_service.get_daily_session(student_id)}


@router.get("/lexicon/phase0/status")
def lexicon_phase0_status(student_id: str = Query(...)):
    """获取 Phase 0 状态（含 exam_practice_allowed 字段）。"""
    return {"data": aural_lexicon_service.get_phase0_status(student_id)}


@router.get("/lexicon/phase0/entry-test")
def lexicon_entry_test(student_id: str = Query(...)):
    """获取入口听觉词汇测试词条（40条随机抽样）。"""
    return {"data": aural_lexicon_service.start_entry_test(student_id)}


@router.post("/lexicon/phase0/entry-test/complete")
def lexicon_entry_test_complete(body: _EntryTestResultsIn):
    """提交入口测试结果，决定是否进入 Phase 0。

    DTO 约束: results 只接受 item_id + is_correct，无 listening ability 字段。
    """
    # Validate: no forbidden ability fields in results
    for res in body.results:
        forbidden = {"understanding_stable", "ability_improved", "diagnosis",
                     "material_mastered"} & set(res.keys())
        if forbidden:
            raise HTTPException(
                status_code=422,
                detail=f"禁止字段: {forbidden} (DTO 白名单违规)"
            )
    result = aural_lexicon_service.complete_entry_test(
        body.student_id, body.results, body.threshold
    )
    return {"data": result}


@router.post("/lexicon/phase0/complete")
def lexicon_phase0_complete(body: _Phase0CompleteIn):
    """Phase 0 复测达标，标记完成，开放六级练习。"""
    result = aural_lexicon_service.complete_phase0(
        body.student_id, body.retest_score
    )
    return {"data": result}


@router.post("/lexicon/attempt")
def lexicon_record_attempt(body: _LexAttemptIn):
    """记录词汇 attempt，更新 SRS 调度。

    响应只含 attempt_id + lexical_item_recognized（无 ability 结论）。
    """
    try:
        result = aural_lexicon_service.record_attempt(
            student_id=body.student_id,
            item_id=body.item_id,
            task_type=body.task_type,
            is_correct=body.is_correct,
            response=body.response,
            response_latency_ms=body.response_latency_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"data": result}


@router.get("/exams/{exam_id}/pacing")
def exam_pacing_windows(exam_id: str):
    """返回该套题的答题窗口分段数据（仅 Set 2 可用）。

    用于 Strict Pacing Player：audio currentTime 对齐 window_start_s
    触发 13 秒倒计时，window_end_s 到期自动锁题。
    Set 1 为封卷资产，无分段数据，返回 404。
    """
    import json as _json
    pacing_dir = Path(__file__).resolve().parent / "data" / "pacing"
    pacing_file = pacing_dir / f"{exam_id}_windows.json"
    if not pacing_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"pacing data not found for {exam_id} (sealed or unavailable)"
        )
    data = _json.loads(pacing_file.read_text(encoding="utf-8"))
    return {"data": data}


@router.get("/lexicon/items")
def lexicon_all_items():
    """返回全部 lex_items（用于 transcript 高亮匹配）。不含 SRS 状态。"""
    return {"data": aural_lexicon_service.get_all_items()}


@router.post("/lexicon/harvest")
def lexicon_harvest(body: _HarvestIn):
    """听后采集：将词条加入 SRS 队列。

    D3 红线：gate_type='exam_attempt' 要求 submitted_at IS NOT NULL；
             gate_type='cp_session'  要求 stage='result_final'。
    响应无 ability 结论字段。
    """
    try:
        result = aural_lexicon_service.harvest_word(
            student_id=body.student_id,
            item_id=body.item_id,
            gate_type=body.gate_type,
            gate_id=body.gate_id,
        )
    except ValueError as e:
        code = 403 if "D3_GATE_BLOCKED" in str(e) else 422
        raise HTTPException(status_code=code, detail=str(e))
    return {"data": result}


# ══════════════════════════════════════════════════════════════════════
# Work Order G: Stem Bank + Option Prediction
# ══════════════════════════════════════════════════════════════════════

class _PredictionIn(BaseModel):
    student_id: str
    question_no: int
    predicted_type: Optional[str] = None   # 题型预测（可无）
    selected_answer: Optional[str] = None  # A/B/C/D（可无）


@router.get("/stem-bank/stems")
def stem_bank_list(
    question_type: Optional[str] = Query(None),
    unit_type: Optional[str] = Query(None),
):
    """浏览 Stem Bank（Set 2 only，无正确答案）。
    可按 question_type / unit_type 筛选。
    """
    return {"data": stem_bank_service.get_stems(question_type, unit_type)}


@router.get("/stem-bank/session")
def stem_bank_session(
    count: int = Query(5, ge=1, le=25),
    question_type: Optional[str] = Query(None),
    unit_type: Optional[str] = Query(None),
):
    """获取随机练习会话（N 道题，无正确答案）。
    客户端在学生提交后调用 /stem-bank/predict 取得正确答案。
    """
    return {"data": stem_bank_service.get_practice_session(count, question_type, unit_type)}


@router.post("/stem-bank/predict")
def stem_bank_predict(body: _PredictionIn):
    """提交题型预测 + 答案选择，返回正确答案与 is_correct。

    此端点是唯一返回 correct_answer 的路径。
    """
    try:
        result = stem_bank_service.record_prediction(
            student_id=body.student_id,
            question_no=body.question_no,
            predicted_type=body.predicted_type,
            selected_answer=body.selected_answer,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"data": result}


@router.get("/stem-bank/stats")
def stem_bank_stats(student_id: str = Query(...)):
    """学生各题型预测准确率统计（无 ability 结论文案）。"""
    return {"data": stem_bank_service.get_student_stats(student_id)}


# ══════════════════════════════════════════════════════════════════════
# Work Order H: Dashboard
# ══════════════════════════════════════════════════════════════════════

@router.get("/dashboard")
def student_dashboard(student_id: str = Query(...)):
    """聚合仪表盘数据（Phase 0 状态、今日词汇、题型统计、近期答题）。

    Copy 规范：所有字段为事实数字，无 ability 结论文案。
    """
    return {"data": dashboard_service.get_dashboard(student_id)}
