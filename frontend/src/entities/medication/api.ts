import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function useDrugClassFallback(drugName: string, existingClass?: string | null, medicationId?: string): string | null {
  const qc = useQueryClient()
  const { data } = useQuery({
    queryKey: ['drug-class-fallback', drugName],
    queryFn: async () => {
      const { data } = await apiClient.get<DrugSearchItem[]>('/health/medications/drug-search', {
        params: { q: drugName },
      })
      const cls = data[0]?.drug_class ?? null
      // 찾은 값을 DB에 저장해 다음부터 API 호출 없이 DB에서 바로 반환
      if (cls && medicationId) {
        await apiClient.patch(`/users/me/medications/${medicationId}`, { drug_name: drugName, drug_class: cls })
        qc.invalidateQueries({ queryKey: KEY })
      }
      return cls
    },
    enabled: !existingClass && drugName.trim().length >= 2,
    staleTime: Infinity,
  })
  return existingClass ?? data ?? null
}
import { apiClient } from '@/shared/api/client'
import type { DrugSearchItem, MedicationItem } from './model'

const KEY = ['medications'] as const

export function useMedications() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: MedicationItem[] }>('/users/me/medications')
      return data.data
    },
  })
}

type MedicationBody = { drug_name: string; dosage?: string; frequency?: string; instructions?: string; drug_class?: string | null; start_date?: string | null; end_date?: string | null; scheduled_time?: string | null; record_type?: number | null; memo?: string | null }

export function useAddMedication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: MedicationBody) => {
      const { data } = await apiClient.post<{ data: MedicationItem }>('/users/me/medications', body)
      return data.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['calendar'] })
      qc.invalidateQueries({ queryKey: ['notification', 'list'] })
    },
  })
}

export function useUpdateMedication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: { id: string } & MedicationBody) => {
      await apiClient.patch(`/users/me/medications/${id}`, body)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useDrugSearch(query: string) {
  return useQuery({
    queryKey: ['drug-search', query],
    queryFn: async () => {
      const { data } = await apiClient.get<DrugSearchItem[]>('/health/medications/drug-search', { params: { q: query } })
      return data
    },
    enabled: query.trim().length >= 2,
    staleTime: 1000 * 60 * 5,
  })
}

export function useScheduleMedication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, start_date, end_date, scheduled_time = '08:00:00', interval_days = 1 }: {
      id: string; start_date: string; end_date: string; scheduled_time?: string; interval_days?: number
    }) => {
      await apiClient.post(`/users/me/medications/${id}/schedule`, { start_date, end_date, scheduled_time, interval_days })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['calendar'] }),
  })
}

export function useDeleteMedication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/users/me/medications/${id}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['calendar'] })
      qc.invalidateQueries({ queryKey: ['notification', 'list'] })
    },
  })
}
