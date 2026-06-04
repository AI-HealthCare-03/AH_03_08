export interface CalendarEvent {
  id: string
  medication_id: string
  event_date: string
  scheduled_time: string
  status: 'PENDING' | 'TAKEN' | 'MISSED'
  taken_at: string | null
  note: string | null
  created_at: string
}

export interface MonthlyCalendar {
  year: number
  month: number
  total: number
  items: CalendarEvent[]
}