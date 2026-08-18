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
    | 'answer_select'
    | 'answer_change'
    | 'audio_play'
    | 'audio_pause'
    | 'audio_seek'
    | 'audio_replay'
    | 'audio_ended'
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
