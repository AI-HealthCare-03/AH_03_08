import { ChevronRight } from 'lucide-react'
import { GuideStatusBadge } from '@/shared/ui/GuideStatusBadge'
import type { Guide } from '@/entities/guide/model'
import { formatGuideDate, guideDisplayTitle, guidePreviewText, guideShortId } from './guide-utils'
import { useRecord } from '@/entities/medical-record/api'

const TYPE_BADGE: Record<string, { bg: string; color: string; label: string }> = {
  prescription: { bg: '#EFF6FF', color: '#1D4ED8', label: '처방전' },
  medicine_bag: { bg: '#FFF7ED', color: '#C2410C', label: '약봉투' },
  pill_photo: { bg: '#F0FDF4', color: '#15803D', label: '낱알약' },
}

interface GuideListCardProps {
  guide: Guide
  selected?: boolean
  onSelect: () => void
}

export function GuideListCard({ guide, selected, onSelect }: GuideListCardProps) {
  const { data: record } = useRecord(guide.record_id)
  const medCount = record?.parsed_data?.medications?.length ?? null
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-2xl border bg-white p-4 text-left shadow-sm transition-all ${
        selected
          ? 'border-brand-primary ring-1 ring-brand-primary/25 bg-brand-lightest/30'
          : 'border-gray-100 hover:border-gray-200 hover:shadow-md'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            {record && TYPE_BADGE[record.record_type] && (
              <span
                className="shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold"
                style={{ background: TYPE_BADGE[record.record_type].bg, color: TYPE_BADGE[record.record_type].color }}
              >
                {TYPE_BADGE[record.record_type].label}
              </span>
            )}
            <h3 className="text-sm font-semibold text-gray-900">
              {guideDisplayTitle(guide, record).replace(/^(처방전|약봉투|낱알약)\s*/, '')}
            </h3>
            <GuideStatusBadge status={guide.status} />
          </div>
          <p className="text-xs text-gray-400">
            {guideShortId(guide.id)}
            {guide.created_at ? ` · ${formatGuideDate(guide.created_at)}` : ''}
          </p>
          <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">{guidePreviewText(guide)}</p>
          <div className="flex flex-wrap gap-2 pt-1">
            <span className="inline-flex items-center rounded-full bg-brand-lightest px-2.5 py-1 text-xs font-medium text-brand-dark">
              의약품 {medCount ?? '-'}종
            </span>
            <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">
              복약·생활 가이드
            </span>
          </div>
        </div>
        <ChevronRight className="h-5 w-5 shrink-0 text-gray-300 mt-1" />
      </div>
    </button>
  )
}
