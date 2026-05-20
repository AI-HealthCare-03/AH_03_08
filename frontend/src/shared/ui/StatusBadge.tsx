import { Badge } from '@/components/ui/badge'
import type { RecordStatus } from '@/shared/types'

const statusConfig: Record<RecordStatus, { label: string; className: string }> = {
  pending:    { label: '대기중', className: 'bg-[#FAEEDA] text-[#854F0B] hover:bg-[#FAEEDA]' },
  processing: { label: '처리중', className: 'bg-[#FAEEDA] text-[#854F0B] hover:bg-[#FAEEDA]' },
  completed:  { label: '완료',   className: 'bg-[#EAF3DE] text-[#3B6D11] hover:bg-[#EAF3DE]' },
  failed:     { label: '실패',   className: 'bg-[#FCEBEB] text-[#A32D2D] hover:bg-[#FCEBEB]' },
}

interface StatusBadgeProps {
  status: RecordStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { label, className } = statusConfig[status]
  return (
    <Badge className={`text-xs font-medium px-2 py-0.5 rounded-full ${className}`}>
      {label}
    </Badge>
  )
}
