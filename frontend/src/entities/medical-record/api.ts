import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { MedicalRecord } from './model'
import type { PaginatedResponse, RecordType } from '@/shared/types'

const KEYS = {
  all: ['medical-records'] as const,
  list: () => [...KEYS.all, 'list'] as const,
  detail: (id: number) => [...KEYS.all, 'detail', id] as const,
}

async function fetchRecords(): Promise<MedicalRecord[]> {
  const { data } = await apiClient.get<PaginatedResponse<MedicalRecord>>('/medical-records')
  return data.items
}

async function uploadRecord(payload: { file: File; record_type: RecordType }): Promise<MedicalRecord> {
  const form = new FormData()
  form.append('file', payload.file)
  form.append('record_type', payload.record_type)
  const { data } = await apiClient.post<MedicalRecord>('/medical-records/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export function useMedicalRecords() {
  return useQuery({
    queryKey: KEYS.list(),
    queryFn: fetchRecords,
  })
}

export function useUploadRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: uploadRecord,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list() }),
  })
}
