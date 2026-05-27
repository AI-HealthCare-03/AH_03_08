export interface ChatSession {
  id: string
  user_id: number
  guide_id: string | null
  title: string | null
  created_at: string
  last_active_at: string
  last_message_content: string | null
  last_message_role: string | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  error?: boolean
}

export interface Guide {
  id: string
  record_id: string
  status: string
}
