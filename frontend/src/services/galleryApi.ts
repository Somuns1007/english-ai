// Gallery requests reuse HttpOnly login cookies and the existing teacher credential.
import { getTeacherToken } from './listeningApi'

export type GalleryStatus = 'pending' | 'approved' | 'rejected'
export interface GalleryImage {
  id: string
  image_url: string
  thumbnail_url: string
  caption: string
  status: GalleryStatus
  created_at: string
  reviewed_at: string | null
  reject_reason?: string | null
  user_email?: string
  file_size?: number
  like_count: number
  liked: boolean
}
export type GallerySort = 'latest' | 'popular'
export interface GalleryPage { data: GalleryImage[]; total: number; page: number; page_size: number }

export async function galleryRequest<T>(path: string, options: RequestInit = {}, admin = false): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.method && options.method !== 'GET') headers.set('X-Auth-Request', '1')
  if (admin) headers.set('X-Teacher-Token', getTeacherToken())
  let response: Response
  try {
    response = await fetch(`/api/${path}`, { ...options, headers, credentials: 'include', cache: 'no-store' })
  } catch { throw new Error('无法连接服务器，请稍后重试。') }
  if (!response.ok) {
    const result = await response.json().catch(() => ({})) as { detail?: unknown }
    if (response.status === 401) throw new Error('登录状态已失效，请重新登录。')
    if (response.status === 413) throw new Error('图片不能超过 10MB。')
    throw new Error(response.status < 500 && typeof result.detail === 'string'
      ? result.detail : '操作失败，请稍后重试。')
  }
  return response.json() as Promise<T>
}

export async function toggleLike(imageId: string): Promise<{ liked: boolean; like_count: number }> {
  return galleryRequest(`gallery/images/${imageId}/like`, { method: 'POST' })
}

export async function galleryBlob(url: string, admin: boolean): Promise<string> {
  // Fixed same-origin API paths only; never attach a teacher secret to an arbitrary URL.
  if (!/^\/api\/gallery\/images\/[0-9a-f]{32}(\/thumbnail)?$/.test(url)) throw new Error('图片地址无效')
  const response = await fetch(url, { credentials: 'include', cache: 'no-store',
    headers: admin ? { 'X-Teacher-Token': getTeacherToken() } : {} })
  if (!response.ok) throw new Error('图片暂时无法查看，请刷新页面。')
  return URL.createObjectURL(await response.blob())
}
