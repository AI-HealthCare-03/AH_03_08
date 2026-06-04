import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { register as registerApi, registerSchema, type RegisterFormValues } from '@/features/auth/register-api'

const STEPS = ['계정 정보', '개인 정보'] as const

export function RegisterPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [serverError, setServerError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false)

  const {
    register,
    handleSubmit,
    trigger,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { gender: undefined },
  })

  const selectedGender = watch('gender')
  const password = watch('password')
  const passwordConfirm = watch('passwordConfirm')
  const passwordMismatch = !!passwordConfirm && password !== passwordConfirm

  async function handleNext() {
    const step1Fields: (keyof RegisterFormValues)[] = ['email', 'password', 'passwordConfirm']
    const valid = await trigger(step1Fields)
    if (valid && !passwordMismatch) setStep(1)
  }

  async function onSubmit(values: RegisterFormValues) {
    setServerError(null)
    try {
      await registerApi(values)
      navigate('/auth/login', { state: { registered: true } })
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setServerError(msg ?? '회원가입 중 오류가 발생했습니다.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10" style={{ background: 'var(--color-background-primary)' }}>
      <div className="w-full max-w-sm">
        {/* 로고 */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold" style={{ color: '#1D9E75' }}>메디로그</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
            건강 기록 기반 관리가이드
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          {/* 헤더 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-800">회원가입</h2>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
              {step === 0
                ? '로그인에 사용할 이메일과 비밀번호를 입력해주세요.'
                : '서비스 맞춤 설정을 위한 기본 정보를 입력해주세요.'}
            </p>
          </div>

          {/* 스텝 인디케이터 */}
          <div className="flex items-center gap-2 mb-6">
            {STEPS.map((label, i) => (
              <div key={label} className="flex items-center gap-2 flex-1">
                <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                  i <= step ? 'text-white' : 'text-gray-400 bg-gray-100'
                }`} style={i <= step ? { background: '#1D9E75' } : {}}>
                  {i + 1}
                </div>
                <span className={`text-xs font-medium ${i <= step ? 'text-gray-700' : 'text-gray-400'}`}>
                  {label}
                </span>
                {i < STEPS.length - 1 && (
                  <div className={`flex-1 h-px ${i < step ? 'bg-[#1D9E75]' : 'bg-gray-200'}`} />
                )}
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            {/* ── Step 1: 계정 정보 ── */}
            {step === 0 && (
              <>
                <Field label="이메일" error={errors.email?.message}>
                  <input
                    {...register('email')}
                    type="email"
                    placeholder="example@email.com"
                    autoComplete="email"
                    className={inputCls(!!errors.email)}
                  />
                </Field>

                <Field label="비밀번호" error={errors.password?.message}
                  hint="대·소문자·숫자·특수문자 각 1개 이상, 8자 이상">
                  <div className="relative">
                    <input
                      {...register('password')}
                      type={showPassword ? 'text' : 'password'}
                      placeholder="비밀번호 입력"
                      autoComplete="new-password"
                      className={inputCls(!!errors.password) + ' pr-10'}
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
                </Field>

                <Field
                  label="비밀번호 확인"
                  error={passwordMismatch ? '비밀번호가 일치하지 않습니다' : errors.passwordConfirm?.message}
                >
                  <div className="relative">
                    <input
                      {...register('passwordConfirm')}
                      type={showPasswordConfirm ? 'text' : 'password'}
                      placeholder="비밀번호 재입력"
                      autoComplete="new-password"
                      className={inputCls(passwordMismatch || !!errors.passwordConfirm) + ' pr-10'}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPasswordConfirm(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      tabIndex={-1}
                    >
                      {showPasswordConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </Field>

                <Button
                  type="button"
                  className="w-full mt-1 text-white font-medium"
                  style={{ background: '#1D9E75' }}
                  onClick={handleNext}
                >
                  다음
                </Button>
              </>
            )}

            {/* ── Step 2: 개인 정보 ── */}
            {step === 1 && (
              <>
                <Field label="이름" error={errors.name?.message}>
                  <input
                    {...register('name')}
                    type="text"
                    placeholder="실명 입력"
                    className={inputCls(!!errors.name)}
                  />
                </Field>

                <Field label="성별" error={errors.gender?.message}>
                  <div className="grid grid-cols-2 gap-2">
                    {(['MALE', 'FEMALE'] as const).map((g) => (
                      <button
                        key={g}
                        type="button"
                        onClick={() => setValue('gender', g, { shouldValidate: true })}
                        className={`py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                          selectedGender === g
                            ? 'border-[#1D9E75] text-[#1D9E75] bg-[#E1F5EE]'
                            : 'border-gray-200 text-gray-500 hover:border-gray-300'
                        }`}
                      >
                        {g === 'MALE' ? '남성' : '여성'}
                      </button>
                    ))}
                  </div>
                </Field>

                <Field label="생년월일" error={errors.birth_date?.message}>
                  <input
                    {...register('birth_date')}
                    type="date"
                    className={inputCls(!!errors.birth_date)}
                  />
                </Field>

                <Field label="전화번호" error={errors.phone_number?.message}
                  hint="010-0000-0000 형식">
                  <input
                    {...register('phone_number')}
                    type="tel"
                    placeholder="010-0000-0000"
                    className={inputCls(!!errors.phone_number)}
                  />
                </Field>

                {serverError && (
                  <p className="text-xs text-red-500 text-center">{serverError}</p>
                )}

                <div className="flex gap-2 mt-1">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={() => setStep(0)}
                  >
                    이전
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 text-white font-medium"
                    style={{ background: '#1D9E75' }}
                  >
                    {isSubmitting ? '가입 중...' : '회원가입'}
                  </Button>
                </div>
              </>
            )}
          </form>
        </div>

        {/* 로그인 링크 */}
        <p className="text-center text-sm mt-5" style={{ color: 'var(--color-text-tertiary)' }}>
          이미 계정이 있으신가요?{' '}
          <Link to="/auth/login" className="font-medium hover:underline underline-offset-2" style={{ color: '#1D9E75' }}>
            로그인
          </Link>
        </p>
      </div>
    </div>
  )
}

// ── 공통 컴포넌트 ──

function inputCls(hasError: boolean) {
  return `w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-colors
    focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/20
    ${hasError ? 'border-red-400' : 'border-gray-200'}`
}

interface FieldProps {
  label: string
  error?: string
  hint?: string
  children: React.ReactNode
}
function Field({ label, error, hint, children }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      {children}
      {hint && !error && <p className="text-xs text-gray-400">{hint}</p>}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}
