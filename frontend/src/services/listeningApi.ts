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

// ---------- Phase 5B: 证据画像 ----------

export function fetchProfile(studentId: string): Promise<any> {
  return request<any>(
    `/api/listening/profile?student_id=${encodeURIComponent(studentId)}`
  )
}

// ---------- Phase 6: Expression Bridge 跨语境训练 ----------

export interface ExpressionCard {
  expression_id: string
  expression: string
  meaning: string
  communicative_function: string
  source_exam_id: string
  source_question_id: string
  source_sentence: string
  source_type: string
  review_status: string
  scenario_count: number
  done_count: number
  correct_count: number
}

export interface ScenarioQuestion {
  question: string
  options: Record<string, string>
}

export interface ScenarioPublic {
  scenario_id: string
  expression_id: string
  scenario: string
  communicative_function: string
  difficulty: string
  source_type: string
  review_status: string
  questions: Record<'scene' | 'meaning' | 'key_info', ScenarioQuestion>
  has_audio: boolean
  last_attempt: { all_correct: boolean; created_at: string } | null
}

export interface ExpressionDetail extends ExpressionCard {
  source_unit_id: string
  related_expressions: string[]
  selection_reasons: string[]
  scenarios: ScenarioPublic[]
}

export interface ExpressionSubmitResult {
  attempt_id: string
  correct: { scene: boolean | null; meaning: boolean | null; key_info: boolean | null; all: boolean }
  answers: Record<string, string>
  evidence: {
    strength: number
    level: string
    factors: Record<string, number>
    verification_level: string
    source_quality: string
  }
  text: string
  target_expression: string
  target_surface: string
  related_expressions: string[]
  expression_meaning: string | null
  source_type: string
}

export interface AudioMeta {
  scenario_id: string
  file: string
  voice_id: string
  provider: string
  speed: string
  generated_at: string
  source_type: string
}

export function fetchExpressions(studentId: string): Promise<ExpressionCard[]> {
  return request<ExpressionCard[]>(
    `/api/listening/expressions?student_id=${encodeURIComponent(studentId)}`
  )
}

export function fetchExpressionDetail(
  expressionId: string,
  studentId: string
): Promise<ExpressionDetail> {
  return request<ExpressionDetail>(
    `/api/listening/expressions/${encodeURIComponent(expressionId)}?student_id=${encodeURIComponent(studentId)}`
  )
}

export function scenarioAudioUrl(scenarioId: string): string {
  return `/api/listening/expressions/scenarios/${encodeURIComponent(scenarioId)}/audio`
}

export function fetchScenarioAudioMeta(scenarioId: string): Promise<AudioMeta> {
  return request<AudioMeta>(
    `/api/listening/expressions/scenarios/${encodeURIComponent(scenarioId)}/audio-meta`
  )
}

export function submitExpressionScenario(
  scenarioId: string,
  body: {
    student_id: string
    answers: Record<string, string>
    listen_count_before_submit: number
    reveal_used: boolean
    duration_ms: number
  }
): Promise<ExpressionSubmitResult> {
  return request<ExpressionSubmitResult>(
    `/api/listening/expressions/scenarios/${encodeURIComponent(scenarioId)}/submit`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }
  )
}

export function markExpressionReplay(attemptId: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(
    `/api/listening/expression-attempts/${encodeURIComponent(attemptId)}/replayed`,
    { method: 'POST' }
  )
}

export interface EarlyReveal {
  text: string
  target_expression: string
  target_surface: string
}

export function revealScenarioEarly(scenarioId: string): Promise<EarlyReveal> {
  return request<EarlyReveal>(
    `/api/listening/expressions/scenarios/${encodeURIComponent(scenarioId)}/reveal-early`,
    { method: 'POST' }
  )
}

// ---------- Phase 6.1/7: 教师审核(口令鉴权, 密钥只在服务端) ----------

const TEACHER_TOKEN_KEY = 'aq_teacher_token'

export function getTeacherToken(): string {
  return sessionStorage.getItem(TEACHER_TOKEN_KEY) || ''
}

export function setTeacherToken(token: string) {
  sessionStorage.setItem(TEACHER_TOKEN_KEY, token)
}

export function clearTeacherToken() {
  sessionStorage.removeItem(TEACHER_TOKEN_KEY)
}

function teacherHeaders(json = true): Record<string, string> {
  const h: Record<string, string> = { 'X-Teacher-Token': getTeacherToken() }
  if (json) h['Content-Type'] = 'application/json'
  return h
}

export function teacherFetchExpressions(): Promise<any[]> {
  return request<any[]>('/api/listening/teacher/expressions', { headers: teacherHeaders(false) })
}

export function teacherFetchExpressionDetail(expressionId: string): Promise<any> {
  return request<any>(
    `/api/listening/teacher/expressions/${encodeURIComponent(expressionId)}`,
    { headers: teacherHeaders(false) }
  )
}

export function teacherUpdateExpression(
  expressionId: string,
  fields: { meaning?: string; communicative_function?: string; related_expressions?: string[] }
): Promise<any> {
  return request<any>(
    `/api/listening/teacher/expressions/${encodeURIComponent(expressionId)}`,
    { method: 'PUT', headers: teacherHeaders(), body: JSON.stringify(fields) }
  )
}

export function teacherUpdateScenario(
  scenarioId: string,
  fields: {
    text?: string
    scenario?: string
    communicative_function?: string
    difficulty?: string
    target_surface?: string
  }
): Promise<any> {
  return request<any>(
    `/api/listening/teacher/scenarios/${encodeURIComponent(scenarioId)}`,
    { method: 'PUT', headers: teacherHeaders(), body: JSON.stringify(fields) }
  )
}

export function teacherReviewExpression(
  expressionId: string,
  action: 'approve' | 'reject'
): Promise<any> {
  return request<any>(
    `/api/listening/teacher/expressions/${encodeURIComponent(expressionId)}/review`,
    { method: 'POST', headers: teacherHeaders(), body: JSON.stringify({ action }) }
  )
}

export function teacherReviewScenario(
  scenarioId: string,
  action: 'approve' | 'reject'
): Promise<any> {
  return request<any>(
    `/api/listening/teacher/scenarios/${encodeURIComponent(scenarioId)}/review`,
    { method: 'POST', headers: teacherHeaders(), body: JSON.stringify({ action }) }
  )
}

export function teacherRegenerateAudio(scenarioId: string): Promise<AudioMeta> {
  return request<AudioMeta>(
    `/api/listening/teacher/scenarios/${encodeURIComponent(scenarioId)}/regenerate-audio`,
    { method: 'POST', headers: teacherHeaders(), body: '{}' }
  )
}

// ---------- Phase 7: 真实语料 ingestion ----------

export interface CorpusAsset {
  asset_id: string
  title: string
  source_name: string
  source_url: string | null
  license: string
  permission_status: string
  source_type: string
  file_path: string
  duration_ms: number | null
  uploaded_at: string
  review_status: string
  pipeline_status: string
  pipeline_error: string | null
  raw_asr_text: string | null
  cleaned_text: string | null
  asr_confidence: number | null
  transcript_status: string
  revision: number
  reviewed_at: string | null
}

export interface CorpusClip {
  clip_id: string
  asset_id: string
  start_ms: number
  end_ms: number
  transcript: string
  context_before: string
  context_after: string
  speaker_info: string | null
  scenario_tags: string[]
  communicative_function: string | null
  difficulty: string | null
  expression_matches: {
    expression_id: string
    matched_text: string
    match_type: string
    status: string
  }[]
  review_status: string
  revision: number
  revisions_log: { revision: number; edited_at: string; changed_fields: string[]; substantive: boolean }[]
  reviewed_at: string | null
}

export function corpusUploadAsset(
  file: File,
  meta: {
    title: string
    source_name: string
    source_url?: string
    license: string
    permission_status: string
  }
): Promise<CorpusAsset> {
  const q = new URLSearchParams({
    title: meta.title,
    source_name: meta.source_name,
    license: meta.license,
    permission_status: meta.permission_status
  })
  if (meta.source_url) q.set('source_url', meta.source_url)
  const form = new FormData()
  form.append('file', file)
  return request<CorpusAsset>(`/api/listening/teacher/corpus/assets?${q}`, {
    method: 'POST',
    headers: { 'X-Teacher-Token': getTeacherToken() },
    body: form
  })
}

export function corpusListAssets(): Promise<CorpusAsset[]> {
  return request<CorpusAsset[]>('/api/listening/teacher/corpus/assets', {
    headers: teacherHeaders(false)
  })
}

export function corpusAssetDetail(
  assetId: string
): Promise<CorpusAsset & { clips: CorpusClip[] }> {
  return request<CorpusAsset & { clips: CorpusClip[] }>(
    `/api/listening/teacher/corpus/assets/${encodeURIComponent(assetId)}`,
    { headers: teacherHeaders(false) }
  )
}

export function corpusAssetAudioUrl(assetId: string): string {
  // 音频经 <audio> 标签直连, token 走 query(服务端支持 header 或 query)
  return `/api/listening/teacher/corpus/assets/${encodeURIComponent(assetId)}/audio?token=${encodeURIComponent(getTeacherToken())}`
}

export function corpusUpdateAsset(
  assetId: string,
  fields: Partial<Pick<CorpusAsset, 'title' | 'source_name' | 'source_url' | 'license' | 'permission_status'>>
): Promise<CorpusAsset> {
  return request<CorpusAsset>(
    `/api/listening/teacher/corpus/assets/${encodeURIComponent(assetId)}`,
    { method: 'PUT', headers: teacherHeaders(), body: JSON.stringify(fields) }
  )
}

export function corpusReviewAsset(
  assetId: string,
  action: 'approve' | 'reject'
): Promise<CorpusAsset> {
  return request<CorpusAsset>(
    `/api/listening/teacher/corpus/assets/${encodeURIComponent(assetId)}/review`,
    { method: 'POST', headers: teacherHeaders(), body: JSON.stringify({ action }) }
  )
}

export function corpusRunStep(
  assetId: string,
  step: 'run-asr' | 'run-segmentation' | 'run-matching'
): Promise<any> {
  return request<any>(
    `/api/listening/teacher/corpus/assets/${encodeURIComponent(assetId)}/${step}`,
    { method: 'POST', headers: teacherHeaders(), body: '{}' }
  )
}

export function corpusUpdateClip(
  clipId: string,
  fields: {
    start_ms?: number
    end_ms?: number
    transcript?: string
    scenario_tags?: string[]
    communicative_function?: string
    difficulty?: string
    speaker_info?: string
  }
): Promise<CorpusClip> {
  return request<CorpusClip>(
    `/api/listening/teacher/corpus/clips/${encodeURIComponent(clipId)}`,
    { method: 'PUT', headers: teacherHeaders(), body: JSON.stringify(fields) }
  )
}

export function corpusReviewClip(
  clipId: string,
  action: 'approve' | 'reject'
): Promise<CorpusClip> {
  return request<CorpusClip>(
    `/api/listening/teacher/corpus/clips/${encodeURIComponent(clipId)}/review`,
    { method: 'POST', headers: teacherHeaders(), body: JSON.stringify({ action }) }
  )
}
