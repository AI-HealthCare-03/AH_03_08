import { useState } from 'react'
import { MessageCircle, Share2, Volume2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { GuideStatusBadge } from '@/shared/ui/GuideStatusBadge'
import type { Guide } from '@/entities/guide/model'
import { formatGuideDate, guideDisplayTitle, guideShortId } from './guide-utils'
import { toast } from '@/shared/lib/toast'
import { useNavigate } from 'react-router-dom'
import { useChatSessions, useCreateSession } from '@/entities/chatbot/api'
import { useMedicalRecords } from '@/entities/medical-record/api'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'

interface GuideDetailHeaderProps {
  guide: Guide
}

export function GuideDetailHeader({ guide }: GuideDetailHeaderProps) {
  const navigate = useNavigate()
  const { data: sessions } = useChatSessions()
  const { mutateAsync: createSession, isPending } = useCreateSession()
  const { data: records } = useMedicalRecords()
  const [speaking, setSpeaking] = useState(false)

  async function handleShare() {
    const url = `${window.location.origin}/guide?id=${guide.id}`
    try {
      if (navigator.share) {
        await navigator.share({ title: guideDisplayTitle(guide), url })
      } else {
        await navigator.clipboard.writeText(url)
        toast.success('링크가 복사되었습니다.')
      }
    } catch {
      /* user cancelled */
    }
  }

  function handleTts() {
  if (speaking && !window.speechSynthesis.paused) {
    window.speechSynthesis.pause()
    setSpeaking(false)
  } else if (window.speechSynthesis.paused) {
    window.speechSynthesis.resume()
    setSpeaking(true)
  } else {
    const text = guide.summary_text?.trim() || ''
    if (!text) {
      toast.error('읽을 내용이 없습니다.')
      return
    }
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'ko-KR'
    utterance.rate = 1.0
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    window.speechSynthesis.speak(utterance)
    setSpeaking(true)
  }
}

  async function handleAskChatbot() {
    const existing = sessions?.find(s => s.guide_id === guide.id)
    if (existing) {
      navigate(`/chatbot/${existing.id}`)
      return
    }
    const record = records?.find(r => r.id === guide.record_id)
    const meta = record ? RECORD_TYPE_META[record.record_type] : null
    const placeName = record?.record_type === 'medicine_bag'
      ? record.parsed_data?.pharmacy
      : record?.parsed_data?.hospital
    const title = meta ? (placeName ? `${placeName} ${meta.label}` : meta.label) : guideDisplayTitle(guide)
    try {
      const newSession = await createSession({ guide_id: guide.id, title })
      navigate(`/chatbot/${newSession.id}`)
    } catch {
      toast.error('챗봇 세션 생성에 실패했습니다.')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-lg font-bold text-gray-900">{guideDisplayTitle(guide)}</h2>
            <GuideStatusBadge status={guide.status} />
          </div>
          <p className="mt-1 text-xs text-gray-500">
            {guideShortId(guide.id)}
            {guide.created_at ? ` · ${formatGuideDate(guide.created_at)}` : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className={`gap-1.5 text-xs h-9 ${speaking ? 'border-brand-primary text-brand-primary bg-brand-lightest/30' : 'border-gray-200'}`}
            onClick={handleTts}
          >
            <Volume2 className="h-4 w-4" />
            {speaking ? '일시정지' : '음성으로 듣기'}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs h-9 border-gray-200"
            onClick={handleAskChatbot}
            disabled={isPending}
          >
            <MessageCircle className="h-4 w-4" />
            {isPending ? '연결 중...' : '챗봇에 묻기'}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs h-9 border-gray-200"
            onClick={handleShare}
          >
            <Share2 className="h-4 w-4" />
            공유하기
          </Button>
        </div>
      </div>
    </div>
  )
}
