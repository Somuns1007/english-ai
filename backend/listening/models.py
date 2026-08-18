# -*- coding: utf-8 -*-
"""听力诊断系统 Pydantic 模型。字段命名与 03_技术实现与数据结构.md 对齐。"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------- 内容层(题库) ----------


class OptionItem(BaseModel):
    label: str
    text: str  # 来源解析 PDF 的选项中文译文
    text_en: Optional[str] = None  # 英文选项原材料中不存在, 不得编造


class TeacherAnnotation(BaseModel):
    evidence_text: Optional[str] = None
    key_locators: list[str] = Field(default_factory=list)
    paraphrase: list[dict] = Field(default_factory=list)
    distractors: list[dict] = Field(default_factory=list)


class AiAnnotation(BaseModel):
    review_status: Literal["pending_review", "approved", "rejected"] = "pending_review"
    generated_by: Optional[str] = None
    generated_at: Optional[str] = None
    diagnosis_candidates: list[dict] = Field(default_factory=list)
    dictation_template: Optional[dict] = None
    chunking: list[dict] = Field(default_factory=list)


class Question(BaseModel):
    id: str
    unit_id: str
    exam_id: str
    section: str
    number: int
    question_text: Optional[str] = None
    question_text_zh: Optional[str] = None
    options: list[OptionItem] = Field(default_factory=list)
    correct_answer: Optional[str] = None
    source_explanation: Optional[str] = None
    distractor_analysis: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_start_ms: Optional[int] = None
    evidence_end_ms: Optional[int] = None
    timing_status: Literal["verified", "needs_review"] = "needs_review"
    review_status: Literal["reviewed", "needs_review"] = "needs_review"
    teacher_annotation: TeacherAnnotation = Field(default_factory=TeacherAnnotation)
    ai_annotation: AiAnnotation = Field(default_factory=AiAnnotation)


class Unit(BaseModel):
    id: str
    exam_id: str
    section: str
    type: Literal["conversation", "passage", "recording"]
    order: int
    title: str
    audio_start_ms: Optional[int] = None
    audio_end_ms: Optional[int] = None
    timing_status: Literal["verified", "needs_review"] = "needs_review"
    transcript: Optional[str] = None
    transcript_status: Literal["verified", "needs_review"] = "needs_review"
    questions: list[Question] = Field(default_factory=list)


class Exam(BaseModel):
    id: str
    exam_type: str = "cet6"
    title: str
    year: int
    month: int
    set_no: int
    audio_path: str
    duration_ms: Optional[int] = None
    status: str = "published"
    question_count: int = 0
    units: list[Unit] = Field(default_factory=list)


class ExamSummary(BaseModel):
    """听力首页卡片: 不含题目内容, 附带学生完成状态。"""

    id: str
    exam_type: str
    title: str
    year: int
    month: int
    set_no: int
    duration_ms: Optional[int] = None
    question_count: int
    section_count: int
    has_audio: bool
    completed: bool = False
    last_score: Optional[int] = None
    last_submitted_at: Optional[str] = None


# ---------- 学生行为层 ----------


class AttemptCreate(BaseModel):
    student_id: str = "anonymous"
    exam_id: str
    mode: Literal["exam_mode", "practice_mode"] = "practice_mode"


class AnswerUpsert(BaseModel):
    first_answer: Optional[str] = None
    final_answer: Optional[str] = None
    first_answer_at: Optional[str] = None
    last_answer_at: Optional[str] = None
    change_count: int = 0
    dwell_ms: int = 0


# ---------- 行为事件流水(与学生错因判定分离, 只做客观记录) ----------


class BehaviorEventIn(BaseModel):
    """单条行为事件。question_id 为空表示音频级事件。

    event_type 约定:
      question_enter / question_leave      题目停留(dwell 证据)
      answer_select / answer_change        选项选择与修改
      audio_play / audio_pause / audio_seek / audio_replay / audio_ended
      hint_open                            提示使用(practice 模式, payload 带 level)
    """

    event_type: str
    question_id: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    client_at: Optional[str] = None  # 客户端时钟, 可能不准, 仅供参考


class BehaviorEventBatch(BaseModel):
    student_id: str = "anonymous"
    events: list[BehaviorEventIn] = Field(default_factory=list)


class AttemptAnswer(BaseModel):
    attempt_id: str
    question_id: str
    first_answer: Optional[str] = None
    final_answer: Optional[str] = None
    first_answer_at: Optional[str] = None
    change_count: int = 0
    is_first_correct: Optional[bool] = None
    relisten_count: int = 0
    max_hint_level: int = 0


class Attempt(BaseModel):
    id: str
    student_id: str
    exam_id: str
    mode: str
    started_at: str
    submitted_at: Optional[str] = None
    score: Optional[int] = None


class DiagnosisIn(BaseModel):
    student_id: str = "anonymous"
    attempt_id: str
    question_id: str
    student_tags: list[str] = Field(default_factory=list)
    final_tags: list[str] = Field(default_factory=list)


class TrainingResultIn(BaseModel):
    student_id: str = "anonymous"
    question_id: str
    training_type: str
    pre_result: Optional[bool] = None
    post_result: Optional[bool] = None
