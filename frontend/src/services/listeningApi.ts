// 听力模块 API 封装, 与 WritingView 一致使用原生 fetch + 相对路径
import type {
  ExamSummary,
  UnitWithQuestions,
  Attempt,
  BehaviorEvent,
  ExamMode,
  InProgressAttempt,
  SubmitResult,
  ReviewOverview,
  HintContent,
  CandidatesResult,
  SelfDiagnosisOption
} from '../types/listening'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  let result: { data?: T; detail?: string } | null = null
  try {
    result = await response.json()
  } catch {
    result = null
  }
  if (!response.ok) {
    throw new Error(result?.detail || `请求失败，状态码：${response.status}`)
  }
  return (result as { data: T }).data
}

export function fetchExams(studentId = 'anonymous'): Promise<ExamSummary[]> {
  return request<ExamSummary[]>(
    `/api/listening/exams?student_id=${encodeURIComponent(studentId)}`
  )
}

export function fetchExamQuestions(examId: string): Promise<UnitWithQuestions[]> {
  return request<UnitWithQuestions[]>(
    `/api/listening/exams/${encodeURIComponent(examId)}/questions`
  )
}

export function createAttempt(
  examId: string,
  mode: 'exam_mode' | 'practice_mode',
  studentId = 'anonymous'
): Promise<Attempt> {
  return request<Attempt>('/api/listening/attempts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, exam_id: examId, mode })
  })
}

export function audioUrl(examId: string): string {
  return `/api/listening/audio/${encodeURIComponent(examId)}`
}

export function findInProgressAttempt(
  examId: string,
  mode: ExamMode,
  studentId: string
): Promise<InProgressAttempt | null> {
  const q = new URLSearchParams({ exam_id: examId, mode, student_id: studentId })
  return request<InProgressAttempt | null>(`/api/listening/attempts/in-progress?${q}`)
}

export function saveAnswer(
  attemptId: string,
  questionId: string,
  answer: {
    first_answer: string | null
    final_answer: string | null
    first_answer_at: string | null
    last_answer_at: string | null
    change_count: number
    dwell_ms: number
  }
): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/answers/${encodeURIComponent(questionId)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(answer)
    }
  )
}

export function submitAttempt(attemptId: string): Promise<SubmitResult> {
  return request<SubmitResult>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/submit`,
    { method: 'POST' }
  )
}

export function postBehaviorEvents(
  attemptId: string,
  studentId: string,
  events: BehaviorEvent[],
  keepalive = false
): Promise<{ saved: number }> {
  return request<{ saved: number }>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/events`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, events }),
      keepalive
    }
  )
}

// ---------- Phase 3: 复盘 ----------

export function fetchReviewOverview(attemptId: string): Promise<ReviewOverview> {
  return request<ReviewOverview>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/review`
  )
}

export function openHint(
  attemptId: string,
  questionId: string,
  level: number
): Promise<HintContent> {
  return request<HintContent>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/questions/${encodeURIComponent(questionId)}/hint`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level })
    }
  )
}

export function retryQuestion(
  attemptId: string,
  questionId: string,
  answer: string
): Promise<{ is_correct: boolean }> {
  return request<{ is_correct: boolean }>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/questions/${encodeURIComponent(questionId)}/retry`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer })
    }
  )
}

export function fetchCandidates(
  attemptId: string,
  questionId: string
): Promise<CandidatesResult> {
  return request<CandidatesResult>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/questions/${encodeURIComponent(questionId)}/candidates`
  )
}

export function fetchSelfDiagnosisOptions(): Promise<SelfDiagnosisOption[]> {
  return request<SelfDiagnosisOption[]>('/api/listening/self-diagnosis-options')
}

export function fetchTagDictionary(): Promise<
  Record<string, { zh: string; layer: string }>
> {
  return request<Record<string, { zh: string; layer: string }>>(
    '/api/listening/tag-dictionary'
  )
}

export function saveDiagnosis(
  attemptId: string,
  questionId: string,
  studentTags: string[],
  finalTags: string[],
  studentId: string
): Promise<{ id: string; revision: number }> {
  return request<{ id: string; revision: number }>('/api/listening/diagnoses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      attempt_id: attemptId,
      question_id: questionId,
      student_tags: studentTags,
      final_tags: finalTags
    })
  })
}

// ---------- Phase 4: 对症训练 ----------

export function fetchTrainingPlan(
  attemptId: string,
  questionId: string
): Promise<any> {
  return request<any>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/questions/${encodeURIComponent(questionId)}/training-plan`
  )
}

export function fetchTrainingContent(
  attemptId: string,
  questionId: string,
  type: string
): Promise<any> {
  return request<any>(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/questions/${encodeURIComponent(questionId)}/training/${encodeURIComponent(type)}`
  )
}

export function checkTraining(
  attemptId: string,
  questionId: string,
  type: string,
  payload: Record<string, unknown>
): Promise<{ score: number; result: boolean; error_details: any[]; answer?: any }> {
  return request(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/questions/${encodeURIComponent(questionId)}/training/${encodeURIComponent(type)}/check`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }
  )
}

export function blindRetest(
  attemptId: string,
  questionId: string,
  answer: string
): Promise<{ is_correct: boolean; hints_during_retest: number; note: string }> {
  return request(
    `/api/listening/attempts/${encodeURIComponent(attemptId)}/questions/${encodeURIComponent(questionId)}/blind-retest`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer })
    }
  )
}

export function saveTrainingResult(body: {
  student_id: string
  question_id: string
  training_type: string
  attempt_id?: string
  diagnosis_id?: string
  input: Record<string, unknown>
  result: boolean
  score: number
  error_details: any[]
  hints_used: number
  duration_ms: number
}): Promise<{ id: string }> {
  return request<{ id: string }>('/api/listening/training-results', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
}

export function fetchMistakes(
  studentId: string,
  filters: {
    mastery?: string
    tag?: string
    section?: string
    trained?: boolean
    retested?: boolean
  } = {}
): Promise<any[]> {
  const q = new URLSearchParams({ student_id: studentId })
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  return request<any[]>(`/api/listening/mistakes?${q}`)
}
