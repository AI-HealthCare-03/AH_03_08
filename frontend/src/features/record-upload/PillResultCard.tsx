// frontend/src/features/record-upload/PillResultCard.tsx
interface PillResultCardProps {
  drugName: string | null
  diClassNo: string | null
  diEtcOtcCode: string | null
}

export function PillResultCard({ drugName, diClassNo, diEtcOtcCode }: PillResultCardProps) {
  return (
    <div className="mt-4 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
      <p className="mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">약품 정보</p>
      <div className="space-y-2">
        <div>
          <p className="text-xs text-gray-500">약품명</p>
          <p className="text-sm font-medium text-gray-800">{drugName ?? '-'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">효능/효과</p>
          <p className="text-sm font-medium text-gray-800">{diClassNo ?? '-'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">구분</p>
          <p className="text-sm font-medium text-gray-800">{diEtcOtcCode ?? '-'}</p>
        </div>
      </div>
    </div>
  )
}