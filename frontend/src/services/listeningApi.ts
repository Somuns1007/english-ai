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
  // Phase 7.7: 自建录音授权链
  consent_id: string | null
  speaker_ids: string[]
  commercial_permission: boolean
  editing_permission: boolean
  ai_processing_permission: boolean
  recorded_at: string | null
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
    match_method?: string
    confidence?: number
    status: string
    note?: string
    reviewed_at?: string
  }[]
  review_status: string
  revision: number
  // Phase 7.7: revision 拆分 — 内容版(实质修改才变)与元数据版(标签调整)
  content_revision?: number
  metadata_revision?: number
  revisions_log: {
    content_revision?: number
    metadata_revision?: number
    revision?: number
    edited_at: string
    changed_fields: string[]
    bump?: 'content' | 'metadata'
    substantive?: boolean
  }[]
  reviewed_at: string | null
  accent: string | null
  speaker_count: number | null
  speech_rate: string | null
  listening_features: string[]
  origin: string
}

export function corpusUploadAsset(
  file: File,
  meta: {
    title: string
    source_name: string
    source_url?: string
    license: string
    permission_status: string
    // Phase 7.7: 自建录音授权链(permission_status=owned 时必填 consent_id 才能批准)
    consent_id?: string
    speaker_ids?: string[]
    commercial_permission?: boolean
    editing_permission?: boolean
    ai_processing_permission?: boolean
    recorded_at?: string
  }
): Promise<CorpusAsset> {
  const q = new URLSearchParams({
    title: meta.title,
    source_name: meta.source_name,
    license: meta.license,
    permission_status: meta.permission_status
  })
  if (meta.source_url) q.set('source_url', meta.source_url)
  if (meta.consent_id) q.set('consent_id', meta.consent_id)
  if (meta.speaker_ids?.length) q.set('speaker_ids', meta.speaker_ids.join(','))
  if (meta.commercial_permission) q.set('commercial_permission', 'true')
  if (meta.editing_permission) q.set('editing_permission', 'true')
  if (meta.ai_processing_permission) q.set('ai_processing_permission', 'true')
  if (meta.recorded_at) q.set('recorded_at', meta.recorded_at)
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
  fields: Partial<Pick<CorpusAsset,
    'title' | 'source_name' | 'source_url' | 'license' | 'permission_status' |
    'consent_id' | 'speaker_ids' | 'commercial_permission' |
    'editing_permission' | 'ai_processing_permission' | 'recorded_at'>>
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
    accent?: string
    speaker_count?: number
    speech_rate?: string
    listening_features?: string[]
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

// ---------- Phase 7.6: 手工 clip / 匹配确认 / 学生端语料 ----------

export function corpusCreateClip(
  assetId: string,
  fields: { start_ms: number; end_ms: number; transcript?: string; speaker_info?: string }
): Promise<CorpusClip> {
  return request<CorpusClip>(
    `/api/listening/teacher/corpus/assets/${encodeURIComponent(assetId)}/clips`,
    { method: 'POST', headers: teacherHeaders(), body: JSON.stringify(fields) }
  )
}

export function corpusReviewClipMatch(
  clipId: string,
  expressionId: string,
  action: 'approve' | 'reject'
): Promise<CorpusClip> {
  return request<CorpusClip>(
    `/api/listening/teacher/corpus/clips/${encodeURIComponent(clipId)}/matches`,
    { method: 'POST', headers: teacherHeaders(), body: JSON.stringify({ expression_id: expressionId, action }) }
  )
}

// Phase 7.7: 教师手动建立匹配(含 communicative_equivalent), 直接 approved,
// match_method=teacher_judgement。规则匹配器永不自动产生此类关联。
export function corpusAddClipMatch(
  clipId: string,
  fields: {
    expression_id: string
    matched_text: string
    match_type: 'exact_expression' | 'target_surface' | 'related_expression' | 'communicative_equivalent'
    note?: string
  }
): Promise<CorpusClip> {
  return request<CorpusClip>(
    `/api/listening/teacher/corpus/clips/${encodeURIComponent(clipId)}/matches`,
    { method: 'POST', headers: teacherHeaders(), body: JSON.stringify({ action: 'add', ...fields }) }
  )
}

export interface StudentCorpusClip {
  clip_id: string
  start_ms: number
  end_ms: number
  transcript: string
  scenario_tags: string[]
  communicative_function: string | null
  difficulty: string | null
  accent: string | null
  speaker_count: number | null
  speech_rate: string | null
  listening_features: string[]
  expression_matches: {
    expression_id: string
    matched_text: string
    match_type: string
    status: string
  }[]
  attribution: {
    asset_id: string
    title: string
    source_name: string
    source_url: string | null
    license: string
    source_type: string
  }
}

export function corpusStudentClips(): Promise<StudentCorpusClip[]> {
  return request<StudentCorpusClip[]>('/api/listening/corpus/clips')
}

export function corpusStudentClipAudioUrl(clipId: string): string {
  // 学生端音频由服务端按 clip 区间精确切片, 无需 token
  return `/api/listening/corpus/clips/${encodeURIComponent(clipId)}/audio`
}

// ---------- V2.1 Exam Mode(audio_only) ----------

import type { V2ExamSummary, V2Paper } from '../types/listening'

export function fetchV2Exams(): Promise<V2ExamSummary[]> {
  return request<V2ExamSummary[]>('/api/listening/v2/exams')
}

export function fetchV2Paper(examId: string): Promise<V2Paper> {
  return request<V2Paper>(
    `/api/listening/v2/exams/${encodeURIComponent(examId)}/paper`
  )
}

// ---------- V2.2 Continuous Practice(Pilot) ----------
// 教学语义: round2 答对 = recovered_after_full_replay(完整重听后恢复),
// 不展示逐题对错/正确答案; profile_eligible=false, 不进画像。

export interface V2PracticeMaterialSummary {
  material_id: string
  exam_id: string
  title: string
  check_count: number
  has_audio: boolean
  data_status: string
  student_release_allowed: boolean
}

export interface V2PracticeCheck {
  check_id: string
  target_dimension: string
  question: string
  options: { label: string; text: string }[]
}

export interface V2PracticeBundle {
  material_id: string
  exam_id: string
  title: string
  audio: { scope: string; url: string; start_ms: number; end_ms: number }
  checks: V2PracticeCheck[]
}

export interface V2PracticeState {
  session_id: string
  material_id: string
  stage:
    | 'intro' | 'option_preview' | 'first_pass' | 'check_round_1'
    | 'blind_full_replay' | 'check_round_2' | 'result_final'
  pass_attempt_count: number
  replay_count: number
  first_pass_valid: boolean
  preview: Record<string, unknown>
  content_drifted: boolean
  profile_eligible: boolean
  first_pass_score?: { correct: number; total: number }
  round2_checks?: { check_id: string; question: string; options: { label: string; text: string }[] }[]
  result?: {
    first_pass_score: { correct: number; total: number }
    recovered: { correct: number; total: number }
    display: string
    observations: string[]
    note: string
  }
}

export function fetchV2PracticeMaterials(): Promise<V2PracticeMaterialSummary[]> {
  return request<V2PracticeMaterialSummary[]>('/api/listening/v2/practice/materials')
}

export function fetchV2PracticeBundle(materialId: string): Promise<V2PracticeBundle> {
  return request<V2PracticeBundle>(
    `/api/listening/v2/practice/materials/${encodeURIComponent(materialId)}`
  )
}

export function createV2PracticeSession(
  materialId: string, studentId = 'anonymous'
): Promise<{ session_id: string; stage: string }> {
  return request('/api/listening/v2/practice/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, material_id: materialId })
  })
}

export function findV2PracticeSession(
  materialId: string, studentId = 'anonymous'
): Promise<{ session_id: string } | null> {
  const q = new URLSearchParams({ material_id: materialId, student_id: studentId })
  return request(`/api/listening/v2/practice/sessions/find?${q}`)
}

export function fetchV2PracticeState(sessionId: string): Promise<V2PracticeState> {
  return request(`/api/listening/v2/practice/sessions/${encodeURIComponent(sessionId)}`)
}

export interface CpEvent {
  event_type: string
  payload?: Record<string, unknown>
  client_at?: string
}

export function postV2PracticeEvents(
  sessionId: string, events: CpEvent[], studentId = 'anonymous', keepalive = false
): Promise<{ saved: number }> {
  return request(`/api/listening/v2/practice/sessions/${encodeURIComponent(sessionId)}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, events }),
    keepalive
  })
}

export function submitV2PracticeRound1(
  sessionId: string, answers: Record<string, string>
): Promise<{ first_pass_score: { correct: number; total: number } }> {
  return request(`/api/listening/v2/practice/sessions/${encodeURIComponent(sessionId)}/round1`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers })
  })
}

// ---------- V2.C Aural Lexicon (CET Track) ----------

import type {
  LexItem,
  LexSessionResponse,
  Phase0Status,
  EntryTestItems,
  LexAttemptResult
} from '../types/listening'

export function fetchLexSession(studentId = 'anonymous'): Promise<LexSessionResponse> {
  return request<LexSessionResponse>(
    `/api/listening/lexicon/session?student_id=${encodeURIComponent(studentId)}`
  )
}

export function fetchPhase0Status(studentId = 'anonymous'): Promise<Phase0Status> {
  return request<Phase0Status>(
    `/api/listening/lexicon/phase0/status?student_id=${encodeURIComponent(studentId)}`
  )
}

export function fetchEntryTestItems(studentId = 'anonymous'): Promise<EntryTestItems> {
  return request<EntryTestItems>(
    `/api/listening/lexicon/phase0/entry-test?student_id=${encodeURIComponent(studentId)}`
  )
}

export function submitEntryTestResults(
  studentId: string,
  results: { item_id: string; is_correct: boolean }[],
  threshold = 0.70
): Promise<{ student_id: string; entry_score: number; phase0_entered: boolean; status: string }> {
  return request(
    '/api/listening/lexicon/phase0/entry-test/complete',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, results, threshold })
    }
  )
}

export function recordLexAttempt(
  studentId: string,
  itemId: string,
  taskType: 'hear_identify' | 'micro_dictation' | 'speed_ladder',
  isCorrect: boolean
): Promise<LexAttemptResult> {
  return request<LexAttemptResult>('/api/listening/lexicon/attempt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      item_id: itemId,
      task_type: taskType,
      is_correct: isCorrect
    })
  })
}

export function submitV2PracticeRound2(
  sessionId: string, answers: Record<string, string>
): Promise<{
  first_pass_score: { correct: number; total: number }
  recovered: { correct: number; total: number }
  display: string
}> {
  return request(`/api/listening/v2/practice/sessions/${encodeURIComponent(sessionId)}/round2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers })
  })
}
