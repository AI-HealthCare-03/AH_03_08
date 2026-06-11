import { useParams } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'
import { SessionList } from '@/features/chatbot-conversation/SessionList'
import { ChatWindow } from '@/features/chatbot-conversation/ChatWindow'

export function ChatbotPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* 모바일: 목록 OR 채팅 */}
      <div className="md:hidden">
        {!sessionId ? (
          <SessionList selectedSessionId={sessionId} />
        ) : (
          <div className="h-[calc(100svh-9.5rem)]">
            <ChatWindow key={sessionId} sessionId={sessionId} />
          </div>
        )}
      </div>

      {/* 데스크탑: 목록 + 채팅 */}
      <div className="hidden md:grid md:grid-cols-[300px_1fr] md:gap-6 md:items-start">
        <div>
          <SessionList selectedSessionId={sessionId} />
        </div>
        <div className="sticky top-8 h-[calc(100svh-5.5rem)]">
          {sessionId ? (
            <ChatWindow key={sessionId} sessionId={sessionId} />
          ) : (
            <div className="h-full rounded-2xl border border-dashed border-gray-200 bg-gray-50/80 flex flex-col items-center justify-center gap-3 text-gray-400">
              <MessageCircle className="h-10 w-10" />
              <p className="text-sm font-medium text-gray-500">채팅을 선택하거나 새 채팅을 시작하세요</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
