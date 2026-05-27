import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Send } from 'lucide-react'
import { useAuthStore } from '@/app/providers/auth-store'
import { useCurrentUser } from '@/entities/user/api'
import { useChatSessions, useChatMessages, useGuides } from '@/entities/chatbot/api'
import { useMedicalRecords } from '@/entities/medical-record/api'
import { toast } from '@/shared/lib/toast'
import { MessageBubble, TypingIndicator } from './MessageBubble'
import type { ChatMessage } from '@/entities/chatbot/model'
import type { RecordType } from '@/shared/types'

const WELCOME_MESSAGES: Record<RecordType | 'default', string> = {
  prescription: '안녕하세요 😊\n처방전을 바탕으로 복약 방법, 약물 부작용, 주의사항 등 궁금하신 점을 편하게 물어보세요.',
  medicine_bag: '안녕하세요 😊\n약봉투 정보를 바탕으로 복용 방법, 용량, 주의사항 등 궁금하신 점을 편하게 물어보세요.',
  pill_photo: '안녕하세요 😊\n약 정보를 바탕으로 궁금하신 점을 편하게 물어보세요.',
  default: '안녕하세요 😊\n처방전을 바탕으로 궁금하신 점이 있으면 편하게 물어보세요.',
}

interface Props {
  sessionId: string
}

const WS_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/^http/, 'ws')

export function ChatWindow({ sessionId }: Props) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [wsReady, setWsReady] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const historyLoadedRef = useRef(false)

  const token = useAuthStore((s) => s.accessToken)
  const { data: user } = useCurrentUser()
  const { data: sessions } = useChatSessions()
  const { data: history } = useChatMessages(sessionId)
  const { data: guides } = useGuides()
  const { data: records } = useMedicalRecords()

  const userInitial = user?.name?.[0] ?? '나'
  const session = sessions?.find((s) => s.id === sessionId)
  const guide = guides?.find((g) => g.id === session?.guide_id)
  const record = records?.find((r) => r.id === guide?.record_id)
  const welcomeMessage = WELCOME_MESSAGES[record?.record_type ?? 'default']

  const sessionLabel = session?.title ?? '채팅 세션'

  useEffect(() => {
    if (history && !historyLoadedRef.current) {
      historyLoadedRef.current = true
      setMessages(history.map((m) => ({ ...m, streaming: false, error: false })))
    }
  }, [history])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const connect = useCallback(() => {
    if (!token) return
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.onerror = null
      wsRef.current.close()
    }

    const ws = new WebSocket(`${WS_BASE}/api/v1/chats/${sessionId}/ws?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => setWsReady(true)

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)

      if (data.type === 'token') {
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant' && last.streaming) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.content }]
          }
          return [...prev, { id: `bot-${Date.now()}`, role: 'assistant', content: data.content, streaming: true }]
        })
      } else if (data.type === 'done') {
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant') return [...prev.slice(0, -1), { ...last, streaming: false }]
          return prev
        })
        setIsTyping(false)
      } else if (data.type === 'error') {
        setMessages((prev) => {
          const lastUserIdx = [...prev].reverse().findIndex((m) => m.role === 'user')
          if (lastUserIdx === -1) return prev
          const idx = prev.length - 1 - lastUserIdx
          return prev.map((m, i) => (i === idx ? { ...m, error: true } : m))
        })
        setIsTyping(false)
      }
    }

    ws.onerror = () => {
      toast.error('연결 오류가 발생했습니다.')
      setWsReady(false)
    }

    ws.onclose = () => setWsReady(false)
  }, [sessionId, token])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.onerror = null
        wsRef.current.close()
      }
    }
  }, [connect])

  function send(content: string, messageId?: string) {
    if (!wsReady || isTyping) return
    setMessages((prev) =>
      messageId
        ? prev.map((m) => (m.id === messageId ? { ...m, error: false } : m))
        : [...prev, { id: `user-${Date.now()}`, role: 'user', content }]
    )
    setIsTyping(true)
    wsRef.current!.send(JSON.stringify({ content }))
  }

  function handleSend() {
    const content = input.trim()
    if (!content) return
    setInput('')
    send(content)
  }

  function handleRetry(message: ChatMessage) {
    send(message.content, message.id)
  }

  function handleCancel(messageId: string) {
    setMessages((prev) => prev.filter((m) => m.id !== messageId))
  }

  return (
    <div
      className="flex flex-col bg-white overflow-hidden md:rounded-xl md:border md:border-gray-100 h-full"
    >
      {/* 헤더 */}
      <div className="flex shrink-0 items-center gap-3 border-b border-gray-100 px-4 py-3">
        <button
          onClick={() => navigate('/chatbot')}
          className="md:hidden flex h-8 w-8 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex flex-1 items-center gap-2 min-w-0">
          <span className="truncate font-medium text-gray-800 text-sm">{sessionLabel}</span>
          {!wsReady && (
            <span className="shrink-0 text-xs text-gray-400">연결 중...</span>
          )}
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto space-y-4 bg-gray-50 px-4 py-4">
        <MessageBubble
          message={{ id: 'welcome', role: 'assistant', content: welcomeMessage }}
          userInitial={userInitial}
        />
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            userInitial={userInitial}
            onRetry={handleRetry}
            onCancel={handleCancel}
          />
        ))}
        {isTyping && messages[messages.length - 1]?.role !== 'assistant' && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* 입력창 */}
      <div className="shrink-0 border-t border-gray-100 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="궁금한 점을 입력하세요..."
            disabled={!wsReady || isTyping}
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !wsReady || isTyping}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white transition-opacity disabled:opacity-40"
            style={{ background: '#1D9E75' }}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
