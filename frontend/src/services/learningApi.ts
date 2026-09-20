// Post-listening learning APIs. Identity comes only from the HttpOnly account cookie.
export interface LearningWord { id: string; surface: string; gloss: string; example: string }
export interface LearningSegment {
  id: string; number: number; speaker: string; attempted: boolean; revealed: boolean
  text?: string; vocabulary?: LearningWord[]
  guidance?: { id: string; anchor: string; gloss: string; structure: string; listening: string; transfer: string }[]
  last_attempt?: { text: string; difficulty: string } | null
}
export interface LearningState {
  session_id: string; material_id: string; title: string; finished: boolean
  content_hash: string; source_revision: number; profile_eligible: false
  exposure_status: string; last_segment_id: string | null
  audio: { url: string; scope: string; start_ms: number | null; end_ms: number | null; sentence_timing_verified: false }
  segments: LearningSegment[]
}
export interface LearningMaterial { material_id: string; title: string; segment_count: number }
export interface LearningRecent { session_id: string; title: string; finished: boolean }
export interface LearningCard { card_id: string; surface: string; session_id: string; segment_id: string; next_due: string }
export class LearningError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}
export async function learningRequest<T>(path: string, body?: object, signal?: AbortSignal): Promise<T> {
  const result = await fetch(`/api/listening/learning${path}`, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'include', cache: 'no-store', signal,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'X-Auth-Request': '1' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  const json = await result.json().catch(() => ({}))
  if (!result.ok) throw new LearningError(result.status, typeof json.detail === 'string' ? json.detail : '请求失败，请重试')
  return json.data as T
}
