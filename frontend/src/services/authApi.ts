// Cookie-only auth client and shared reactive user state; no localStorage identity changes.
import { readonly, ref } from 'vue'

export interface AuthUser {
  id: string
  email: string
  created_at: string
  is_active: boolean
}

const user = ref<AuthUser | null>(null)
export const currentUser = readonly(user)

class AuthError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

async function request<T>(path: string, body?: { email: string; password: string } | null): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/auth/${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      credentials: 'include',
      cache: 'no-store',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'X-Auth-Request': '1' },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })
  } catch {
    throw new Error('无法连接服务器，请稍后重试')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new AuthError(typeof data.detail === 'string' ? data.detail : '请求失败，请检查输入后重试', response.status)
  }
  return response.status === 204 ? undefined as T : response.json()
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const result = await request<AuthUser>('login', { email, password })
  user.value = result
  return result
}

export function register(email: string, password: string): Promise<AuthUser> {
  return request<AuthUser>('register', { email, password })
}

export async function logout(): Promise<void> {
  await request<void>('logout', null)
  user.value = null
}

export async function getMe(): Promise<AuthUser | null> {
  try {
    user.value = await request<AuthUser>('me')
    return user.value
  } catch (error) {
    if (error instanceof AuthError && error.status === 401) {
      user.value = null
      return null
    }
    throw error
  }
}
