// 听力模块 API 封装, 与 WritingView 一致使用原生 fetch + 相对路径
import type { ExamSummary, UnitWithQuestions, Attempt } from '../types/listening'

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
