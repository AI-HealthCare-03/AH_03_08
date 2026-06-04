import { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { login, loginSchema, type LoginFormValues } from '@/features/auth/api'

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
      navigate('/home', { replace: true })
    } catch {
      setServerError('이메일 또는 비밀번호가 올바르지 않습니다.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'var(--color-background-primary)' }}>
      <div className="w-full max-w-sm">
        {/* 로고 */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold" style={{ color: '#1D9E75' }}>메디로그</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
            건강 기록 기반 관리가이드
          </p>
        </div>

        {/* 폼 카드 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-6">로그인</h2>

          {justRegistered && (
            <div className="mb-4 rounded-lg px-3 py-2.5 text-xs font-medium" style={{ background: '#E1F5EE', color: '#0F6E56' }}>
              회원가입이 완료됐습니다. 로그인해주세요.
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            {/* 이메일 */}
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
              {errors.email && (
                <p className="text-xs text-red-500">{errors.email.message}</p>
              )}
            </div>

            {/* 비밀번호 */}
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
              {errors.password && (
                <p className="text-xs text-red-500">{errors.password.message}</p>
              )}
            </div>

            {/* 서버 에러 */}
            {serverError && (
              <p className="text-xs text-red-500 text-center">{serverError}</p>
            )}

            {/* 로그인 버튼 */}
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-1 text-white font-medium"
              style={{ background: '#1D9E75' }}
            >
              {isSubmitting ? '로그인 중...' : '로그인'}
            </Button>
          </form>
        </div>

        {/* 회원가입 링크 */}
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
