import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { MedicalRecord, ParsedData } from './model'
import type { RecordType } from '@/shared/types'

const RECORD_TYPE_STR: Record<number, RecordType> = {
  0: 'prescription',
  1: 'medicine_bag',
  2: 'pill_photo',
}

const STATUS_LOWER = (s: string) => s.toLowerCase() as MedicalRecord['status']

function normalizeRecord(raw: Record<string, unknown>): MedicalRecord {
  return {
    ...raw,
    record_type: RECORD_TYPE_STR[raw.record_type as number] ?? raw.record_type,
    status: STATUS_LOWER(raw.status as string),
  } as MedicalRecord
}

const KEYS = {
  all: ['medical-records'] as const,
  list: () => [...KEYS.all, 'list'] as const,
  detail: (id: string) => [...KEYS.all, 'detail', id] as const,
}

async function fetchRecords(): Promise<MedicalRecord[]> {
  const { data } = await apiClient.get<{ items: Record<string, unknown>[]; total: number; page: number }>('/records')
  return data.items.map(normalizeRecord)
}

async function fetchRecord(id: string): Promise<MedicalRecord> {
  const { data } = await apiClient.get<Record<string, unknown>>(`/records/${id}`)
  return normalizeRecord(data)
}

const RECORD_TYPE_INT: Record<RecordType, number> = {
  prescription: 0,
  medicine_bag: 1,
  pill_photo: 2,
}

async function uploadRecord(payload: { file: File; record_type: RecordType }): Promise<MedicalRecord> {
  const form = new FormData()
  form.append('file', payload.file)
  form.append('record_type', String(RECORD_TYPE_INT[payload.record_type]))
  const { data } = await apiClient.post<MedicalRecord>('/records/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

async function deleteRecord(id: string): Promise<void> {
  await apiClient.delete(`/records/${id}`)
}

async function updateRecord(payload: { id: string; parsed_data: ParsedData }): Promise<MedicalRecord> {
  const { data } = await apiClient.put<MedicalRecord>(`/records/${payload.id}`, {
    parsed_data: payload.parsed_data,
  })
  return data
}

async function generateGuide(record_id: string): Promise<{ guide_id: string; status: string }> {
  const { data } = await apiClient.post<{ data: { guide_id: string; status: string } }>('/guides/generate', {
    record_id,
  })
  return data.data
}

export function useMedicalRecords() {
  return useQuery({
    queryKey: KEYS.list(),
    queryFn: fetchRecords,
    refetchInterval: (query) => {
      const records = query.state.data
      if (!records) return false
      const hasPending = records.some(r => r.status === 'pending' || r.status === 'processing')
      return hasPending ? 3000 : false
    },
  })
}

export function useRecord(id: string | null, recordType?: RecordType) {
  return useQuery({
    queryKey: KEYS.detail(id!),
    queryFn: () => fetchRecord(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // pill_photo는 백그라운드 처리라 폴링 불필요
      if (recordType === 'pill_photo') return false
      const status = query.state.data?.status
      if (status === 'pending' || status === 'processing') return 2000
      return false
    },
  })
}

export function useUploadRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: uploadRecord,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list() }),
  })
}

export function useDeleteRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteRecord,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list() }),
  })
}

export function useUpdateRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: updateRecord,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list() }),
  })
}

export function useGenerateGuide() {
  return useMutation({
    mutationFn: generateGuide,
  })
}

async function fetchPillResult(id: string) {
  const { data } = await apiClient.get(`/images/${id}`)
  return data
}

export function usePillResult(id: string | null) {
  return useQuery({
    queryKey: ['pill-result', id],
    queryFn: () => fetchPillResult(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'PENDING' || status === 'PROCESSING') return 2000
      return false
    },
  })
}

async function matchPillByOcr(ocr_texts: string[]) {
  const { data } = await apiClient.post('/images/pill-match', { ocr_texts })
  return data
}

export function usePillMatchOcr() {
  return useMutation({
    mutationFn: matchPillByOcr,
  })
}