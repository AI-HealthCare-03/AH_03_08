import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { User } from './model'

export function useCurrentUser() {
  return useQuery({
    queryKey: ['current-user'],
    queryFn: async () => {
      const { data } = await apiClient.get<User>('/users/me')
      return data
    },
  })
}

export interface UserProfile {
  id: number
  email: string
  name: string
  gender: string | null
  birth_date: string | null
  height_cm: number | null
  weight_kg: number | null
}

export interface AllergyItem {
  id: string
  allergen_name: string
  severity: string
  created_at: string
}

export interface ConditionItem {
  id: string
  condition_name: string
  severity: string
  created_at: string
}

export function useMyProfile() {
  return useQuery({
    queryKey: ['my-profile'],
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: UserProfile }>('/users/me')
      return data.data
    },
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: Partial<Pick<UserProfile, 'name' | 'gender' | 'height_cm' | 'weight_kg'>>) => {
      await apiClient.patch('/users/me', body)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-profile'] }),
  })
}

export function useMyAllergies() {
  return useQuery({
    queryKey: ['my-allergies'],
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-allergies'] }),
  })
}

export function useDeleteAllergy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/users/me/allergies/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-allergies'] }),
  })
}

export function useMyConditions() {
  return useQuery({
    queryKey: ['my-conditions'],
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-conditions'] }),
  })
}

export function useDeleteCondition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/users/me/conditions/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-conditions'] }),
  })
}