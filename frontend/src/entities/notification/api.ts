import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { NotificationItem } from './model'

const KEYS = {
  list: ['notification', 'list'] as const,
}

export function useNotifications() {
  return useQuery({
    queryKey: KEYS.list,
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: NotificationItem[] }>('/notifications')
      return data.data
    },
  })
}

export function useCreateNotification() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: {
      medication_id: string
      title: string
      type: 'push' | 'email'
      scheduled_time: string
    }) => {
      const { data } = await apiClient.post<{ data: NotificationItem }>('/notifications', body)
      return data.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useUpdateNotification() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, is_active, scheduled_time }: { id: string; is_active?: boolean; scheduled_time?: string }) => {
      await apiClient.put(`/notifications/${id}`, { is_active, scheduled_time })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useDeleteNotification() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/notifications/${id}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}