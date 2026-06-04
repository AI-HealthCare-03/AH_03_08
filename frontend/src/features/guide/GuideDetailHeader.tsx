import { MessageCircle, Share2, Volume2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { GuideStatusBadge } from '@/shared/ui/GuideStatusBadge'
import type { Guide } from '@/entities/guide/model'
import { formatGuideDate, guideDisplayTitle, guideShortId } from './guide-utils'
import { toast } from '@/shared/lib/toast'
import { apiClient } from '@/shared/api/client'
import { useNavigate } from 'react-router-dom'

interface GuideDetailHeaderProps {
  guide: Guide
}

export function GuideDetailHeader({ guide }: GuideDetailHeaderProps) {
  const navigate = useNavigate()

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

  async function handleTts() {
    try {
      const response = await apiClient.post(
        `/guides/${guide.id}/assets`,
        { asset_type: 'tts' },
        { responseType: 'blob' },
      )
      const url = URL.createObjectURL(response.data)
      const audio = new Audio(url)
      audio.play()
    } catch {
      toast.error('음성 요청에 실패했습니다.')
    }
  }

  async function handleAskChatbot() {
    const url = `${window.location.origin}/guide?id=${guide.id}`
    try {
      await navigator.clipboard.writeText(url)
    } catch {
      /* ignore */
    }
    toast.success('가이드 링크가 복사되었습니다.', {
      description: '챗봇에서 질문할 때 붙여넣어 주세요.',
    })
    navigate('/chatbot')
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
            className="gap-1.5 text-xs h-9 border-gray-200"
            onClick={handleTts}
          >
            <Volume2 className="h-4 w-4" />
            음성으로 듣기
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs h-9 border-gray-200"
            onClick={handleAskChatbot}
          >
            <MessageCircle className="h-4 w-4" />
            챗봇에 묻기
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