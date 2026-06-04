export interface DashboardData {
  user: {
    name: string
    height_cm: number | null
    weight_kg: number | null
  }
  summary: {
    record_count: number
    active_notification_count: number
  }
  recent_records: {
    record_id: string
    record_type: number
    status: string
    created_at: string
  }[]
  latest_guide: {
    guide_id: string
    status: string
    summary_text: string | null
    created_at: string
  } | null
  today_medications: {
    notification_id: string
    drug_name: string
    scheduled_time: string
    is_active: boolean
  }[]
}