import { useParams } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'
import { SessionList } from '@/features/chatbot-conversation/SessionList'
import { ChatWindow } from '@/features/chatbot-conversation/ChatWindow'

export function ChatbotPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()

  return (
    <div className="flex overflow-hidden -mx-6 -mb-6 -mt-14 md:-mx-10 md:-mb-10 md:-mt-8" style={{ height: '100svh' }}>
      {/* 왼쪽 세션 목록 — 모바일에서 세션 선택 시 숨김 */}
      <div
        className={`${sessionId ? 'hidden md:flex' : 'flex'} md:w-96 w-full shrink-0 flex-col overflow-y-auto border-r border-gray-100 bg-white`}
      >
        <div className="p-4">
          <SessionList selectedSessionId={sessionId} />
        </div>
      </div>

      {/* 오른쪽 채팅창 */}
      {sessionId ? (
        <div className="flex-1 min-w-0 h-full md:p-4">
          <ChatWindow key={sessionId} sessionId={sessionId} />
        </div>
      ) : (
        <div className="hidden md:flex flex-1 items-center justify-center flex-col gap-3 text-gray-300">
          <MessageCircle className="h-12 w-12" />
          <p className="text-sm">채팅을 선택하거나 새 채팅을 시작하세요</p>
        </div>
      )}
    </div>
  )
}
