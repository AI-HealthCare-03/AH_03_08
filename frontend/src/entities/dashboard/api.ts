import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { DashboardData } from './model'

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: DashboardData }>('/dashboard')
      return data.data
    },
  })
}