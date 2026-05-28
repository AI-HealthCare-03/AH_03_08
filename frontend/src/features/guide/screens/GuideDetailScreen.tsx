import { ChevronLeft } from 'lucide-react'
import { GuideStatusBadge } from '@/shared/ui/GuideStatusBadge'
import { PollingStatus } from '@/shared/ui/PollingStatus'
import { EmptyState } from '@/shared/ui/EmptyState'
import type { Guide } from '@/entities/guide/model'
import { GuideContentTabs } from '../GuideContentTabs'
import { GuideDetailHeader } from '../GuideDetailHeader'
import { GuideFeedback } from '../GuideFeedback'

interface GuideDetailScreenProps {
  guide: Guide | undefined
  isLoading: boolean
  showBack?: boolean
  onBack?: () => void
}

/** 와이어프레임 — 가이드 상세 화면 */
export function GuideDetailScreen({
  guide,
  isLoading,
  showBack,
  onBack,
}: GuideDetailScreenProps) {
  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-32 rounded bg-gray-100" />
        <div className="h-12 w-full rounded bg-gray-100" />
        <div className="h-56 rounded-2xl bg-gray-100" />
        <div className="h-40 rounded-2xl bg-gray-100" />
      </div>
    )
  }

  if (!guide) {
    return (
      <EmptyState
        title="가이드를 선택하세요"
        description="목록에서 항목을 선택하면 상세 내용이 표시됩니다."
      />
    )
  }

  if (guide.status === 'processing') {
    return (
      <div className="space-y-4">
        {showBack && onBack && <BackButton onBack={onBack} />}
        <GuideStatusBadge status={guide.status} />
        <PollingStatus message="AI가 복약 가이드를 작성 중입니다..." />
      </div>
    )
  }

  if (guide.status === 'failed') {
    return (
      <div className="space-y-4">
        {showBack && onBack && <BackButton onBack={onBack} />}
        <EmptyState
          title="가이드 생성에 실패했습니다"
          description="의료기록에서 다시 생성해 주세요."
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5 pb-8">
      {showBack && onBack && <BackButton onBack={onBack} />}
      <GuideDetailHeader guide={guide} />
      <GuideContentTabs guide={guide} />
      <GuideFeedback guideId={guide.id} />
    </div>
  )
}

function BackButton({ onBack }: { onBack: () => void }) {
  return (
    <button
      type="button"
      onClick={onBack}
      className="inline-flex items-center gap-1 text-sm font-medium text-brand-primary -ml-1"
    >
      <ChevronLeft className="h-5 w-5" />
      목록으로
    </button>
  )
}
