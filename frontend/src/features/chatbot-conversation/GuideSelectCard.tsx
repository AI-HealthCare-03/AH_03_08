import { FileText, Package } from 'lucide-react'
import type { MedicalRecord } from '@/entities/medical-record/model'

interface Props {
  record: MedicalRecord
  disabled?: boolean
  onClick: () => void
}

const TYPE_CONFIG = {
  prescription: {
    label: '처방전',
    icon: FileText,
    badge: { bg: '#EFF6FF', color: '#1D4ED8' },
    placeKey: 'hospital' as const,
    placeLabel: '병원',
  },
  medicine_bag: {
    label: '약봉투',
    icon: Package,
    badge: { bg: '#FFF7ED', color: '#C2410C' },
    placeKey: 'pharmacy' as const,
    placeLabel: '약국',
  },
  pill_photo: {
    label: '낱알사진',
    icon: FileText,
    badge: { bg: '#F0FDF4', color: '#15803D' },
    placeKey: 'hospital' as const,
    placeLabel: '병원',
  },
}

export function GuideSelectCard({ record, disabled, onClick }: Props) {
  const config = TYPE_CONFIG[record.record_type]
  const Icon = config.icon
  const placeName = record.parsed_data?.[config.placeKey]
  const issuedAt = record.parsed_data?.issued_at
  const diseaseCode = record.parsed_data?.disease_code
  const medCount = record.parsed_data?.medications?.length ?? 0

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3.5 text-left transition-colors hover:bg-gray-100 hover:border-gray-300 disabled:opacity-60"
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white border border-gray-200 mt-0.5">
          <Icon className="h-4 w-4 text-gray-500" />
        </div>
        <div className="min-w-0 flex-1">
          {/* 타입 뱃지 + 장소명 */}
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold"
              style={{ background: config.badge.bg, color: config.badge.color }}
            >
              {config.label}
            </span>
            {placeName && (
              <span className="truncate text-sm font-medium text-gray-800">{placeName}</span>
            )}
          </div>

          {/* 부가 정보 */}
          <div className="mt-1.5 flex items-center gap-2 flex-wrap">
            {issuedAt && (
              <span className="text-xs text-gray-400">
                처방일 {new Date(issuedAt).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })}
              </span>
            )}
            {diseaseCode && (
              <span className="rounded px-1.5 py-0.5 text-xs font-medium"
                style={{ background: '#D1FAE5', color: '#065F46' }}>
                {diseaseCode}
              </span>
            )}
            {medCount > 0 && (
              <span className="text-xs text-gray-400">약 {medCount}종</span>
            )}
          </div>
        </div>
      </div>
    </button>
  )
}
