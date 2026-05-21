import { z } from 'zod'

export const guideSchema = z.object({
  id: z.number(),
  record_id: z.number(),
  content: z.string(),
  tts_url: z.string().nullable(),
  created_at: z.string(),
})

export type Guide = z.infer<typeof guideSchema>
