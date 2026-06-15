import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { googleLogin } from '@/features/auth/api'

export function GoogleCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const code = searchParams.get('code')
    if (!code) {
      navigate('/auth', { replace: true })
      return
    }
    googleLogin(code)
      .then(() => navigate('/home', { replace: true }))
      .catch(() => navigate('/auth', { replace: true }))
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-background-primary)' }}>
      <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Google 로그인 중...</p>
    </div>
  )
}

