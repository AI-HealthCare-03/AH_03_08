import { z } from 'zod'

export const guideStatusSchema = z.enum(['processing', 'done', 'failed'])
export type GuideStatus = z.infer<typeof guideStatusSchema>

export const allergyWarningSchema = z.object({
  drug_name: z.string(),
  warning: z.string(),
})

export const conditionInteractionSchema = z.object({
  drug_name: z.string(),
  condition: z.string(),
  interaction: z.string(),
})

export const guideSchema = z.object({
  id: z.string(),
  record_id: z.string(),
  title: z.string().nullable().optional(),
  status: guideStatusSchema,
  medication_guide: z.string().nullable().optional(),
  lifestyle_guide: z.string().nullable().optional(),
  summary_text: z.string().nullable().optional(),
  allergy_warnings: z.array(allergyWarningSchema).optional().default([]),
  condition_interactions: z.array(conditionInteractionSchema).optional().default([]),
  llm_model: z.string().nullable().optional(),
  created_at: z.string().nullable().optional(),
})

export type Guide = z.infer<typeof guideSchema>

export const GUIDE_STATUS_LABEL: Record<GuideStatus, string> = {
  processing: '생성 중',
  done: '완료',
  failed: '실패',
}
