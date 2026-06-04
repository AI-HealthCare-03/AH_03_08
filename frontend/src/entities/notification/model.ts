export interface NotificationItem {
  id: string
  medication_id: string
  title: string
  type: 'push' | 'email'
  scheduled_time: string
  is_active: boolean
  created_at: string
}