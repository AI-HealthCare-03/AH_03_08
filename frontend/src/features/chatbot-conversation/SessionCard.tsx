import { MessageCircle } from 'lucide-react'
import type { ChatSession } from '@/entities/chatbot/model'

const TYPE_BADGE: Record<string, { bg: string; color: string; label: string }> = {
  prescription: { bg: '#EFF6FF', color: '#1D4ED8', label: '처방전' },
  medicine_bag: { bg: '#FFF7ED', color: '#C2410C', label: '약봉투' },
  pill_photo: { bg: '#F0FDF4', color: '#15803D', label: '낱알약' },
}

interface Props {
  session: ChatSession
  isActive?: boolean
  medicationCount?: number
  diseaseCode?: string | null
  recordType?: string | null
  onClick: () => void
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
  })
}

export function SessionCard({ session, isActive = false, medicationCount = 0, diseaseCode, recordType, onClick }: Props) {
  const label = session.title ?? '채팅 세션'
  const date = formatDate(session.last_active_at)
  const preview = session.last_message_content
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-xl border px-4 py-3 text-left shadow-sm transition-colors
        ${isActive
          ? 'border-[#1D9E75]/30 bg-[#E1F5EE]'
          : 'border-gray-100 bg-white hover:bg-gray-50 active:bg-gray-100'
        }`}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full mt-0.5"
          style={{ background: isActive ? '#1D9E75' : '#E1F5EE' }}
        >
          <MessageCircle className="h-4 w-4" style={{ color: isActive ? '#fff' : '#1D9E75' }} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 min-w-0">
              {recordType && TYPE_BADGE[recordType] && (
                <span
                  className="shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold"
                  style={{ background: TYPE_BADGE[recordType].bg, color: TYPE_BADGE[recordType].color }}
                >
                  {TYPE_BADGE[recordType].label}
                </span>
              )}
              <p className={`truncate text-sm font-medium ${isActive ? 'text-[#0F6E56]' : 'text-gray-800'}`}>
                {label.replace(/^(처방전|약봉투|낱알약)\s*/, '')}
              </p>
            </div>
            <span className="shrink-0 text-xs text-gray-400">{date}</span>
          </div>
          {(diseaseCode || medicationCount > 0) && (
            <div className="mt-1 flex items-center gap-1.5">
              {diseaseCode && (
                <span className="rounded px-1.5 py-0.5 text-xs font-medium"
                  style={{ background: '#D1FAE5', color: '#065F46' }}>
                  {diseaseCode}
                </span>
              )}
              {medicationCount > 0 && (
                <span className="text-xs text-gray-400">처방약 {medicationCount}종</span>
              )}
            </div>
          )}
          {preview ? (
            <p className="mt-1 truncate text-xs text-gray-400">
              {session.last_message_role === 'user' ? '나: ' : 'AI: '}
              {preview}
            </p>
          ) : (
            <p className="mt-1 text-xs text-gray-300">대화를 시작해보세요</p>
          )}
        </div>
      </div>
    </button>
  )
}