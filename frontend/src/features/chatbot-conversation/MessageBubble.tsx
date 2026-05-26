import { AlertTriangle } from 'lucide-react'
import type { ChatMessage } from '@/entities/chatbot/model'

interface Props {
  message: ChatMessage
  userInitial: string
  onRetry?: (message: ChatMessage) => void
  onCancel?: (messageId: string) => void
}

function isWarning(content: string) {
  return content.startsWith('[경고]')
}

function stripWarningMarker(content: string) {
  return content.startsWith('[경고]') ? content.slice('[경고]'.length).trimStart() : content
}

export function MessageBubble({ message, userInitial, onRetry, onCancel }: Props) {
  if (message.role === 'user' && message.error) {
    return (
      <div className="flex flex-col items-end gap-1">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <button
              onClick={() => onCancel?.(message.id)}
              className="rounded px-2 py-0.5 text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              취소
            </button>
            <button
              onClick={() => onRetry?.(message)}
              className="rounded px-2 py-0.5 text-xs font-medium text-red-500 hover:text-red-600 transition-colors"
            >
              재전송
            </button>
          </div>
          <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary/50 px-4 py-2.5">
            <p className="text-sm leading-relaxed text-white whitespace-pre-wrap">{message.content}</p>
          </div>
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
            style={{ background: '#E1F5EE', color: '#0F6E56' }}
          >
            {userInitial}
          </div>
        </div>
        <p className="mr-11 text-xs text-red-400">전송 실패</p>
      </div>
    )
  }

  if (message.role === 'assistant' && isWarning(message.content)) {
    return (
      <div className="flex gap-2.5">
        <BotAvatar />
        <div className="max-w-[80%] rounded-2xl rounded-tl-sm border border-red-200 bg-red-50 px-4 py-3">
          <div className="mb-1 flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
            <span className="text-xs font-semibold text-red-600">주의</span>
          </div>
          <p className="text-sm leading-relaxed text-red-700 whitespace-pre-wrap">{stripWarningMarker(message.content)}</p>
        </div>
      </div>
    )
  }

  if (message.role === 'user') {
    return (
      <div className="flex justify-end gap-2.5">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5">
          <p className="text-sm leading-relaxed text-white whitespace-pre-wrap">{message.content}</p>
        </div>
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
          style={{ background: '#E1F5EE', color: '#0F6E56' }}
        >
          {userInitial}
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-2.5">
      <BotAvatar />
      <div className="max-w-[80%] rounded-2xl rounded-tl-sm border border-gray-100 bg-white px-4 py-2.5 shadow-sm">
        <p className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap">
          {message.content}
          {message.streaming && <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-gray-400" />}
        </p>
      </div>
    </div>
  )
}

function BotAvatar() {
  return (
    <div
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
      style={{ background: '#E1F5EE', color: '#1D9E75' }}
    >
      봇
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div className="flex gap-2.5">
      <BotAvatar />
      <div className="rounded-2xl rounded-tl-sm border border-gray-100 bg-white px-4 py-3 shadow-sm">
        <div className="flex gap-1">
          {[0, 150, 300].map((delay) => (
            <div
              key={delay}
              className="h-2 w-2 animate-bounce rounded-full bg-gray-300"
              style={{ animationDelay: `${delay}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
