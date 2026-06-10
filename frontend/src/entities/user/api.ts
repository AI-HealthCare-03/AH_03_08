import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { User, AllergyItem, ConditionItem } from './model'

const KEYS = {
  me: ['current-user'] as const,
  allergies: ['user', 'allergies'] as const,
  conditions: ['user', 'conditions'] as const,
}

export function useCurrentUser() {
  return useQuery({
    queryKey: KEYS.me,
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: User }>('/users/me')
      return data.data
    },
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { name?: string; gender?: string; height_cm?: number; weight_kg?: number }) => {
      await apiClient.patch('/users/me', body)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.me }),
  })
}

export function useAllergies() {
  return useQuery({
    queryKey: KEYS.allergies,
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: AllergyItem[] }>('/users/me/allergies')
      return data.data
    },
  })
}

export function useAddAllergy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { allergen_name: string; severity: string }) => {
      await apiClient.post('/users/me/allergies', body)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.allergies }),
  })
}

export function useDeleteAllergy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/users/me/allergies/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.allergies }),
  })
}

export function useConditions() {
  return useQuery({
    queryKey: KEYS.conditions,
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: ConditionItem[] }>('/users/me/conditions')
      return data.data
    },
  })
}

export function useAddCondition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { condition_name: string; severity: string }) => {
      await apiClient.post('/users/me/conditions', body)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.conditions }),
  })
}

export function useDeleteCondition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/users/me/conditions/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.conditions }),
  })
}
