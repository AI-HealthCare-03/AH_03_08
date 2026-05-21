import { z } from 'zod'

export const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  name: z.string(),
  profile_image: z.string().nullable(),
})

export type User = z.infer<typeof userSchema>
