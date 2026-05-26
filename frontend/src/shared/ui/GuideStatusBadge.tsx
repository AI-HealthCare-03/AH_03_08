import { Badge } from '@/components/ui/badge'
import { GUIDE_STATUS_LABEL, type GuideStatus } from '@/entities/guide/model'

const statusConfig: Record<GuideStatus, string> = {
  processing: 'bg-[#FAEEDA] text-[#854F0B] hover:bg-[#FAEEDA]',
  done: 'bg-[#EAF3DE] text-[#3B6D11] hover:bg-[#EAF3DE]',
  failed: 'bg-[#FCEBEB] text-[#A32D2D] hover:bg-[#FCEBEB]',
}

export function GuideStatusBadge({ status }: { status: GuideStatus }) {
  return (
    <Badge className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusConfig[status]}`}>
      {GUIDE_STATUS_LABEL[status]}
    </Badge>
  )
}
