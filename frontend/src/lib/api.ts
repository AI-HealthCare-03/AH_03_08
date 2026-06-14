import { requestFcmToken } from '@/lib/firebase'
import { apiClient } from '@/shared/api/client'

// 로그인 성공 직후 실행
async function saveFcmToken() {
  const token = await requestFcmToken()
  if (token) {
    await apiClient.post('/users/fcm-token', { fcm_token: token })
  }
}