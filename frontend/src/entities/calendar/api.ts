import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { CalendarEvent, MonthlyCalendar } from './model'

const KEYS = {
  month: (year: number, month: number) => ['calendar', 'month', year, month] as const,
  day: (date: string) => ['calendar', 'day', date] as const,
}

export function useMonthlyCalendar(year: number, month: number) {
  return useQuery({
    queryKey: KEYS.month(year, month),
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: MonthlyCalendar }>('/calendars', {
        params: { year: String(year), month: String(month) },
      })
      return data.data
    },
  })
}

export function useDailyCalendar(date: string) {
  return useQuery({
    queryKey: KEYS.day(date),
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: CalendarEvent[] }>(`/calendars/${date}`)
      return data.data
    },
  })
}

export function useUpdateEventStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: 'TAKEN' | 'MISSED' | 'PENDING' }) => {
      await apiClient.put(`/calendars/${id}/status`, { status })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}