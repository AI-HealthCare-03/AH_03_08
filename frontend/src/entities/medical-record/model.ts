import { z } from 'zod'
import type { RecordType } from '@/shared/types'

const medicationSchema = z.object({
  name: z.string(),
  dosage: z.coerce.string().nullish(),
  frequency: z.coerce.string().nullish(),
  days: z.number().nullish(),
  instructions: z.string().nullish(),
})

export type Medication = z.infer<typeof medicationSchema>

export const parsedDataSchema = z.object({
  patient_name: z.string().nullish(),
  issued_at: z.string().nullish(),
  hospital: z.string().nullish(),
  pharmacy: z.string().nullish(),
  doctor: z.string().nullish(),
  pharmacist: z.string().nullish(),
  disease_code: z.string().nullish(),
  medications: z.array(medicationSchema).default([]),
})

export type ParsedData = z.infer<typeof parsedDataSchema>

export const medicalRecordSchema = z.object({
  id: z.string(),
  user_id: z.number().optional(),
  record_type: z.enum(['prescription', 'medicine_bag', 'pill_photo']),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  ocr_raw_text: z.string().nullish(),
  parsed_data: parsedDataSchema.nullish(),
  created_at: z.string(),
  // 하위 호환 — 백엔드 미지원 필드
  file_name: z.string().optional(),
  guide_id: z.union([z.string(), z.number()]).nullable().optional(),
})

export type MedicalRecord = z.infer<typeof medicalRecordSchema>

export type RecordStatus = 'pending' | 'processing' | 'completed' | 'failed'

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
