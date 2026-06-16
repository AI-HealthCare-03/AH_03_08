import { z } from 'zod'
import { apiClient } from '@/shared/api/client'

const passwordRule = z
  .string()
  .min(8, '8자 이상이어야 합니다')
  .regex(/[A-Z]/, '대문자를 포함해야 합니다')
  .regex(/[a-z]/, '소문자를 포함해야 합니다')
  .regex(/[0-9]/, '숫자를 포함해야 합니다')
  .regex(/[^a-zA-Z0-9]/, '특수문자를 포함해야 합니다')

export const allergySchema = z.object({
  allergen_name: z.string().min(1),
  severity: z.enum(['mild', 'moderate', 'severe']),
})

export const conditionSchema = z.object({
  condition_name: z.string().min(1),
  severity: z.enum(['mild', 'moderate', 'severe']),
})

const positiveNumber = z.preprocess(
  (v) => (v === '' || v === null || v === undefined ? undefined : Number(v)),
  z.number().positive('양수를 입력해주세요').optional(),
)

export const registerSchema = z
  .object({
    email: z.string().email('올바른 이메일을 입력해주세요'),
    email_token: z.string().min(1, '이메일 인증이 필요합니다'),
    password: passwordRule,
    passwordConfirm: z.string(),
    name: z.string().min(1, '이름을 입력해주세요').max(20, '20자 이하로 입력해주세요'),
    gender: z.enum(['MALE', 'FEMALE'], { message: '성별을 선택해주세요' }),
    birth_date: z.string().refine((val) => {
      const birth = new Date(val)
      const minAge = new Date()
      minAge.setFullYear(minAge.getFullYear() - 14)
      return birth <= minAge
    }, '만 14세 이상만 가입할 수 있습니다'),
    phone_number: z
      .string()
      .regex(
        /^(010-\d{4}-\d{4}|010\d{8}|\+8210\d{8})$/,
        '010-0000-0000 형식으로 입력해주세요',
      ),
    height_cm: positiveNumber,
    weight_kg: positiveNumber,
    allergies: z.array(allergySchema).default([]),
    conditions: z.array(conditionSchema).default([]),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: '비밀번호가 일치하지 않습니다',
    path: ['passwordConfirm'],
  })

export type RegisterFormValues = z.infer<typeof registerSchema>
export type AllergyInput = z.infer<typeof allergySchema>
export type ConditionInput = z.infer<typeof conditionSchema>

export async function sendVerificationEmail(email: string) {
  await apiClient.post('/auth/email/send', { email })
}

export async function verifyEmailCode(email: string, code: string): Promise<string> {
  const res = await apiClient.post('/auth/email/verify', { email, code })
  return res.data.data.email_token as string
}

export async function register(values: RegisterFormValues) {
  const { passwordConfirm: _, ...payload } = values
  await apiClient.post('/auth/signup', payload)
}