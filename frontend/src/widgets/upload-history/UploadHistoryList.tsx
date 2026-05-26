import { StatusBadge } from '@/shared/ui/StatusBadge'
import { Button } from '@/components/ui/button'
import { useMedicalRecords } from '@/entities/medical-record/api'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'
import { useNavigate } from 'react-router-dom'

const TYPE_ICON: Record<string, string> = {
  prescription: 'file-text',
  medicine_bag: 'package',
  pill_photo: 'camera',
}

const TYPE_BADGE: Record<string, { bg: string; color: string }> = {
  prescription: { bg: '#EFF6FF', color: '#1D4ED8' },
  medicine_bag: { bg: '#FFF7ED', color: '#C2410C' },
  pill_photo:   { bg: '#F0FDF4', color: '#15803D' },
}

export function UploadHistoryList() {
  const { data: records, isLoading } = useMedicalRecords()
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 rounded-xl bg-gray-100 animate-pulse" />
        ))}
      </div>
    )
  }

  if (!records?.length) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-400">
        <p className="text-sm">업로드된 기록이 없습니다.</p>
      </div>
    )
  }

  return (
    <ul className="space-y-3">
      {records.map((record) => {
        const meta = RECORD_TYPE_META[record.record_type]
        return (
          <li
            key={record.id}
            className="flex items-start gap-3 rounded-xl bg-white p-4 shadow-sm"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 mt-0.5">
              <RecordIcon name={TYPE_ICON[record.record_type]} />
            </div>

            <div className="flex-1 min-w-0">
              {/* 타입 뱃지 + 병원/약국명 */}
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className="shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold"
                  style={TYPE_BADGE[record.record_type]}
                >
                  {meta.label}
                </span>
                {(() => {
                  const name = record.record_type === 'medicine_bag'
                    ? record.parsed_data?.pharmacy
                    : record.parsed_data?.hospital
                  return name
                    ? <span className="truncate text-sm font-medium text-gray-800">{name}</span>
                    : null
                })()}
              </div>

              {/* 부가 정보 */}
              <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                {record.parsed_data?.issued_at && (
                  <span className="text-xs text-gray-400">
                    처방일 {new Date(record.parsed_data.issued_at).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })}
                  </span>
                )}
                {record.parsed_data?.disease_code && (
                  <span className="rounded px-1.5 py-0.5 text-xs font-medium"
                    style={{ background: '#D1FAE5', color: '#065F46' }}>
                    {record.parsed_data.disease_code}
                  </span>
                )}
                {(record.parsed_data?.medications?.length ?? 0) > 0 && (
                  <span className="text-xs text-gray-400">
                    약 {record.parsed_data!.medications!.length}종
                  </span>
                )}
                {!record.parsed_data?.issued_at && !record.parsed_data?.hospital && !record.parsed_data?.pharmacy && (
                  <span className="text-xs text-gray-400">
                    {new Date(record.created_at).toLocaleDateString('ko-KR')}
                  </span>
                )}
              </div>
            </div>

            <div className="flex flex-col items-end gap-2 shrink-0">
              <StatusBadge status={record.status} />
              {record.status === 'completed' && record.guide_id && (
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs h-7 px-2"
                  onClick={() => navigate(`/guide?id=${record.guide_id}`)}
                >
                  가이드 보기
                </Button>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function RecordIcon({ name }: { name: string }) {
  const paths: Record<string, React.ReactNode> = {
    'file-text': (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9 12h6M9 16h6M7 4H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2h-2M9 4h6v2H9V4z" />
    ),
    package: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    ),
    camera: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9zm9 3a2 2 0 100 4 2 2 0 000-4z" />
    ),
  }
  return (
    <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      {paths[name]}
    </svg>
  )
}
