import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { MedicationItem } from './model'

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

export function useAddMedication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { drug_name: string; dosage?: string; frequency?: string; instructions?: string }) => {
      const { data } = await apiClient.post<{ data: MedicationItem }>('/users/me/medications', body)
      return data.data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useUpdateMedication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: { id: string; drug_name: string; dosage?: string; frequency?: string; instructions?: string }) => {
      await apiClient.patch(`/users/me/medications/${id}`, body)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useDeleteMedication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/users/me/medications/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}
