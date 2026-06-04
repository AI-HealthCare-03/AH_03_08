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
  useAuthStore.getState().setTokens(data.data.access_token)
}

export async function logout() {
  useAuthStore.getState().logout()
}