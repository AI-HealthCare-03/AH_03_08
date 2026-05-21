import { useQuery } from '@tanstack/react-query'
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
