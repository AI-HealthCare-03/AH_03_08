import { z } from 'zod'
import { apiClient } from '@/shared/api/client'
import { useAuthStore } from '@/app/providers/auth-store'

export const loginSchema = z.object({
  email: z.string().email('올바른 이메일을 입력해주세요'),
  password: z.string().min(8, '비밀번호는 8자 이상이어야 합니다'),
})

export type LoginFormValues = z.infer<typeof loginSchema>

export async function login(values: LoginFormValues) {
  const { data } = await apiClient.post('/auth/login', values)
  useAuthStore.getState().setTokens(data.data.access_token, data.data.is_admin)
}

export async function googleLogin(code: string) {
  const { data } = await apiClient.post('/auth/google', { code })
  useAuthStore.getState().setTokens(data.data.access_token, data.data.is_admin)
}

export async function kakaoLogin(code: string) {
  const { data } = await apiClient.post('/auth/kakao', { code })
  useAuthStore.getState().setTokens(data.data.access_token, data.data.is_admin)
}

export async function logout() {
  useAuthStore.getState().logout()
}

export function redirectToGoogle() {
  const params = new URLSearchParams({
    client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    redirect_uri: import.meta.env.VITE_GOOGLE_REDIRECT_URI,
    response_type: 'code',
    scope: 'openid email profile https://www.googleapis.com/auth/calendar',
    access_type: 'offline',
    prompt: 'consent',
  })
  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`
}

export function redirectToKakao() {
  const params = new URLSearchParams({
    client_id: import.meta.env.VITE_KAKAO_CLIENT_ID,
    redirect_uri: import.meta.env.VITE_KAKAO_REDIRECT_URI,
    response_type: 'code',
  })
  window.location.href = `https://kauth.kakao.com/oauth/authorize?${params}`
}