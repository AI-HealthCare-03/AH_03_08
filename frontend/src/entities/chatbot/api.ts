import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import type { ChatSession, ChatMessage, Guide } from './model'

const KEYS = {
  sessions: ['chatbot', 'sessions'] as const,
  guides: ['chatbot', 'guides'] as const,
  messages: (sessionId: string) => ['chatbot', 'messages', sessionId] as const,
}

async function fetchSessions(): Promise<ChatSession[]> {
  const { data } = await apiClient.get<{ total: number; page: number; items: ChatSession[] }>('/chats')
  return data.items
}

async function createSession(payload: { guide_id?: string; title?: string }): Promise<ChatSession> {
  const { data } = await apiClient.post<ChatSession>('/chats', payload)
  return data
}

async function fetchMessages(sessionId: string): Promise<ChatMessage[]> {
  const { data } = await apiClient.get<{ items: ChatMessage[] }>(`/chats/${sessionId}/messages`)
  return data.items
}

async function fetchGuides(): Promise<Guide[]> {
  const { data } = await apiClient.get<{ success: boolean; data: { items: Guide[] } }>('/guides')
  return data.data.items.filter((g) => g.status === 'done')
}

export function useChatSessions() {
  return useQuery({ queryKey: KEYS.sessions, queryFn: fetchSessions })
}

export function useCreateSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.sessions }),
  })
}

export function useChatMessages(sessionId: string) {
  return useQuery({
    queryKey: KEYS.messages(sessionId),
    queryFn: () => fetchMessages(sessionId),
    enabled: !!sessionId,
  })
}

export function useGuides() {
  return useQuery({ queryKey: KEYS.guides, queryFn: fetchGuides })
}
