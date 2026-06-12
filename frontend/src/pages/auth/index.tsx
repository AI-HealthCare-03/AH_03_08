import { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { login, loginSchema, redirectToGoogle, redirectToKakao, type LoginFormValues } from '@/features/auth/api'
import { useAuthStore } from '@/app/providers/auth-store'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const justRegistered = location.state?.registered === true
  const [serverError, setServerError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

  async function onSubmit(values: LoginFormValues) {
    setServerError(null)
    try {
      await login(values)
      const isAdmin = useAuthStore.getState().isAdmin
      navigate(isAdmin ? '/admin' : '/home', { replace: true })
    } catch {
      setServerError('이메일 또는 비밀번호가 올바르지 않습니다.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'var(--color-background-primary)' }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold" style={{ color: '#1D9E75' }}>메디로그</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
            건강 기록 기반 맞춤 서비스
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-6">로그인</h2>

          {justRegistered && (
            <div className="mb-4 rounded-lg px-3 py-2.5 text-xs font-medium" style={{ background: '#E1F5EE', color: '#0F6E56' }}>
              회원가입이 완료되었습니다. 로그인해주세요.
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700">이메일</label>
              <input
                {...register('email')}
                type="email"
                placeholder="example@email.com"
                autoComplete="off"
                className={`w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-colors
                  focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20
                  ${errors.email ? 'border-red-400' : 'border-gray-200'}`}
              />
              {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700">비밀번호</label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="8자 이상 입력"
                  autoComplete="off"
                  className={`w-full rounded-lg border pr-10 px-3 py-2.5 text-sm outline-none transition-colors
                    focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20
                    ${errors.password ? 'border-red-400' : 'border-gray-200'}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
            </div>

            {serverError && <p className="text-xs text-red-500 text-center">{serverError}</p>}

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-1 text-white font-medium"
              style={{ background: '#1D9E75' }}
            >
              {isSubmitting ? '로그인 중...' : '로그인'}
            </Button>
          </form>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-400">또는</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          <div className="flex flex-col gap-3">
            <button
              type="button"
              onClick={redirectToGoogle}
              className="w-full flex items-center justify-center gap-2 rounded-lg border border-gray-200 px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                <path d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Google로 로그인
            </button>

            <button
              type="button"
              onClick={redirectToKakao}
              className="w-full flex items-center justify-center gap-2 rounded-lg border border-yellow-300 px-3 py-2.5 text-sm font-medium text-yellow-900 hover:bg-yellow-50 transition-colors"
              style={{ background: '#FEE500' }}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 0C4.029 0 0 3.136 0 7.004c0 2.493 1.647 4.673 4.125 5.895L3.1 16.5a.25.25 0 0 0 .374.272L8.1 13.94c.296.02.594.031.9.031 4.971 0 9-3.136 9-7.004S13.971 0 9 0z" fill="#3C1E1E"/>
              </svg>
              카카오로 로그인
            </button>
          </div>
        </div>

        <p className="text-center text-sm mt-5" style={{ color: 'var(--color-text-tertiary)' }}>
          아직 계정이 없으신가요?{' '}
          <Link
            to="/auth/register"
            className="font-medium underline-offset-2 hover:underline"
            style={{ color: '#1D9E75' }}
          >
            회원가입
          </Link>
        </p>
      </div>
    </div>
  )
}