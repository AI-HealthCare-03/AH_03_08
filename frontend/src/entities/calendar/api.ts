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
    onSuccess: () => qc.invalidateQueries({ queryKey: ['calendar'] }),
  })
}

export function useCreateCalendarEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { medication_id: string; event_date: string; scheduled_time: string; note?: string }) => {
      const { data } = await apiClient.post<{ data: CalendarEvent }>('/calendars', body)
      return data.data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['calendar'] }),
  })
}

export function useDeleteCalendarEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/calendars/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['calendar'] }),
  })
}