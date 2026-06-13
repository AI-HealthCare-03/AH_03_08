export interface NotificationItem {
  id: string
  medication_id: string
  title: string
  type: 'push' | 'email'
  scheduled_time: string
  is_active: boolean
  end_date: string | null
  created_at: string
}