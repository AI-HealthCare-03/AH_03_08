import axios from 'axios'
import { useAuthStore } from '@/app/providers/auth-store'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  // withCredentials는 BE CORS에서 allow_credentials=True + 명시적 origin 설정 후 활성화
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        // refresh_token은 httpOnly 쿠키로 자동 전송됨
        const { data } = await axios.get(`${BASE_URL}/api/v1/auth/token/refresh`)
        localStorage.setItem('access_token', data.access_token)
        useAuthStore.getState().setTokens(data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(original)
      } catch {
        useAuthStore.getState().logout()
        window.location.href = '/'
      }
    }

    return Promise.reject(error)
  },
)
