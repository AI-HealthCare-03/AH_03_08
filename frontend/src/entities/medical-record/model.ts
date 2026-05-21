import { z } from 'zod'
import type { RecordType } from '@/shared/types'

export const medicalRecordSchema = z.object({
  id: z.number(),
  record_type: z.enum(['prescription', 'medicine_bag', 'pill_photo']),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  file_name: z.string(),
  created_at: z.string(),
  guide_id: z.number().nullable(),
})

export type MedicalRecord = z.infer<typeof medicalRecordSchema>

export const RECORD_TYPE_META: Record<RecordType, { label: string; description: string; icon: string }> = {
  prescription: {
    label: '처방전',
    description: '병원 발급 처방전',
    icon: 'file-text',
  },
  medicine_bag: {
    label: '약봉투',
    description: '용량·복약지도 인쇄',
    icon: 'package',
  },
  pill_photo: {
    label: '낱알 사진',
    description: '약 외형으로 식별',
    icon: 'camera',
  },
}
