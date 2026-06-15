import { useState } from 'react'
import { MessageCircle, Trash2 } from 'lucide-react'
import type { ChatSession } from '@/entities/chatbot/model'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'

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
  onDelete?: () => void
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
  })
}

export function SessionCard({ session, isActive = false, medicationCount = 0, diseaseCode, recordType, onClick, onDelete }: Props) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const label = session.title ?? '채팅 세션'
  const date = formatDate(session.last_active_at)
  const preview = session.last_message_content
  return (
    <>
      <div
        role="button"
        tabIndex={0}
        onClick={onClick}
        onKeyDown={(e) => e.key === 'Enter' && onClick()}
        className={`w-full rounded-xl border px-4 py-3 text-left shadow-sm transition-colors cursor-pointer
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
                  {label.replace(/^(처방전|약봉투|낱알약|낱알 사진)\s*/, '')}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-gray-400">{date}</span>
                {onDelete && (
                  <button
                    onClick={(e) => { e.stopPropagation(); setConfirmOpen(true) }}
                    className="rounded p-1 text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors"
                    aria-label="세션 삭제"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
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
      </div>
      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="대화 삭제"
        description="이 채팅 세션의 대화 내역이 모두 삭제됩니다. 계속하시겠습니까?"
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => onDelete?.()}
      />
    </>
  )
}
