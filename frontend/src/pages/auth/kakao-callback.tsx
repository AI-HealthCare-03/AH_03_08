import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { kakaoLogin } from '@/features/auth/api'

export function KakaoCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const code = searchParams.get('code')
    if (!code) {
      navigate('/auth', { replace: true })
      return
    }
    kakaoLogin(code)
      .then(() => navigate('/home', { replace: true }))
      .catch(() => navigate('/auth', { replace: true }))
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-sm text-gray-500">카카오 로그인 처리 중...</p>
    </div>
  )
}