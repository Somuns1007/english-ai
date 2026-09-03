// 听力模块类型定义, 与后端 listening/models.py 对齐

export interface ExamSummary {
  id: string
  exam_type: string
  title: string
  year: number
  month: number
  set_no: number
  duration_ms: number | null
  question_count: number
  section_count: number
  has_audio: boolean
  completed: boolean
  last_score: number | null
  last_submitted_at: string | null
}

export interface OptionItem {
  label: string
  text: string
  text_en: string | null
}

/** 作答模式下后端返回的题目(已剥离答案与解析) */
export interface PublicQuestion {
  id: string
  unit_id: string
  exam_id: string
  section: string
  number: number
  question_text: string | null
  question_text_zh: string | null
  options: OptionItem[]
  review_status: 'reviewed' | 'needs_review'
}

export interface PublicUnit {
  id: string
  exam_id: string
  section: string
  type: 'conversation' | 'passage' | 'recording'
  order: number
  title: string
  audio_start_ms: number | null
  audio_end_ms: number | null
  timing_status: 'verified' | 'needs_review'
  transcript: string | null
  transcript_status: 'verified' | 'needs_review'
}

export interface UnitWithQuestions {
  unit: PublicUnit
  questions: PublicQuestion[]
}

export interface Attempt {
  id: string
  student_id: string
  exam_id: string
  mode: 'exam_mode' | 'practice_mode'
  started_at: string
  submitted_at: string | null
  score: number | null
}

export type ExamMode = 'exam_mode' | 'practice_mode'

export interface AttemptAnswer {
  attempt_id: string
  question_id: string
  first_answer: string | null
  final_answer: string | null
  first_answer_at: string | null
  last_answer_at: string | null
  change_count: number
  dwell_ms: number
  is_first_correct: boolean | null
  relisten_count: number
  max_hint_level: number
}

/** 行为事件: 只作客观记录, 后端不据此自动判定学生错因 */
export interface BehaviorEvent {
  event_type:
    | 'question_enter'
    | 'question_leave'
    | 'unit_enter'
    | 'unit_leave'
    | 'answer_select'
    | 'answer_change'
    | 'audio_play'
    | 'audio_pause'
    | 'audio_seek'
    | 'audio_replay'
    | 'audio_ended'
    | 'submit'
    | 'hint_open'
  question_id?: string | null
  payload?: Record<string, unknown>
  client_at?: string
}

export interface InProgressAttempt {
  attempt: Attempt
  answers: AttemptAnswer[]
}

export interface SubmitResult {
  attempt: Attempt
  score: number
  question_count: number
}

// ---------- Phase 3: 复盘 ----------

export interface ReviewQuestion {
  question_id: string
  number: number
  section: string
  question_text: string | null
  question_text_zh: string | null
  options: OptionItem[]
  first_answer: string | null
  final_answer: string | null
  is_correct: boolean
  is_first_correct: boolean | null
  change_count: number
  dwell_ms: number
  relisten_count: number
  max_hint_level: number
  retry: { retry_count: number; retry_correct: boolean; last_retry_at: string | null }
  mastery: 'unreviewed' | 'reviewing' | 'improved' | 'mastered' | 'not_mistake'
  diagnosis: {
    id: string | null
    revision: number | null
    student_tags: string[]
    final_tags: string[]
  }
  has_teacher_annotation: boolean
  review_status: string
  correct_answer?: string
}

export interface ReviewOverview {
  attempt: Attempt
  exam_id: string
  title: string
  question_count: number
  units: { unit: PublicUnit; questions: ReviewQuestion[] }[]
}

export interface HintContent {
  level: number
  title: string
  content: Record<string, unknown>
}

export interface DiagnosisCandidate {
  candidate_tag: string
  confidence: number
  evidence: string[]
}

export interface CandidatesResult {
  question_id: string
  candidates: DiagnosisCandidate[]
  note: string | null
  disclaimer: string
  question_level_traps: { option: string; logic: string[]; source_hook: string | null }[]
}

export interface SelfDiagnosisOption {
  code: string
  label: string
  hint: string
}

// ---------- V2.1 Exam Mode(audio_only, 白名单 DTO) ----------

export interface V2ExamSummary {
  id: string
  exam_type: string
  title: string
  question_count: number
  unit_count: number
  has_audio: boolean
  question_delivery: 'audio_only'
  data_status: string
  student_release_allowed: boolean
}

export interface V2PaperOption {
  label: string
  text_en: string
}

export interface V2PaperQuestion {
  question_id: string
  number: number
  options: V2PaperOption[]
}

export interface V2PaperUnit {
  unit_id: string
  section: string
  unit_type: string
  display_title: string
  question_range: [number, number] | null
  questions: V2PaperQuestion[]
}

export interface V2Paper {
  exam_id: string
  question_delivery: 'audio_only'
  audio: { scope: 'whole_set'; url: string }
  units: V2PaperUnit[]
}

// ---------- V2.C Aural Lexicon (CET Track) ----------

export interface LexItem {
  item_id: string
  layer: 'L1' | 'L2' | 'L3'
  surface: string
  gloss: string | null
  audio_asset_id: string | null
}

export interface LexSessionResponse {
  student_id: string
  phase0_active: boolean
  daily_minutes_cap: number
  due_review: LexItem[]
  new_items: LexItem[]
  total_items: number
}

export interface Phase0Status {
  student_id: string
  status: 'not_started' | 'active' | 'completed' | 'forced_exit'
  phase0_active: boolean
  exam_practice_allowed: boolean
  entry_score: number | null
  entry_threshold: number | null
  started_at: string | null
  completed_at: string | null
  forced_exit_at: string | null
  cap_days: number | null
  daily_vocab_minutes: number | null
}

export interface EntryTestItems {
  student_id: string
  items: LexItem[]
  instructions: string
  time_limit_minutes: number
}

export type LexTaskType = 'hear_identify' | 'micro_dictation' | 'speed_ladder'

export interface LexAttemptResult {
  attempt_id: string
  lexical_item_recognized: 0 | 1
}

// ── Stem Bank ─────────────────────────────────────────────────────────

export interface StemItemOption {
  label: string
  text_zh: string
}

/** 单道题干（不含 _correct_answer，客户端从不持有该字段）*/
export interface StemItem {
  question_no: number
  unit_id: string
  unit_type: string
  stem_en: string
  question_type: string
  template_family: string
  options: StemItemOption[]
}

export interface StemTypeAccuracy {
  total: number
  accuracy: number | null
}

export interface StemStats {
  total_predictions: number
  answer_accuracy: number | null
  type_accuracy_by_type: Record<string, StemTypeAccuracy>
}

// ── Pacing ────────────────────────────────────────────────────────────

export interface PacingWindow {
  q: number
  unit_id: string
  section_type: string
  stem_start_s: number
  window_start_s: number
  window_end_s: number
  window_duration_s: number
}
