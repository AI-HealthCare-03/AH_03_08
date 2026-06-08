import { z } from 'zod'

export const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  name: z.string(),
  gender: z.string().nullable().optional(),
  birth_date: z.string().nullable().optional(),
  height_cm: z.number().nullable().optional(),
  weight_kg: z.number().nullable().optional(),
})

export type User = z.infer<typeof userSchema>

export interface AllergyItem {
  id: string
  allergen_name: string
  severity: 'mild' | 'moderate' | 'severe'
  created_at: string
}

export interface ConditionItem {
  id: string
  condition_name: string
  severity: 'mild' | 'moderate' | 'severe'
  created_at: string
}
