// frontend/src/features/record-upload/PillResultCard.tsx
interface PillResultCardProps {
  drugName: string | null
  dlCompany: string | null
  dlMaterial: string | null
  diClassNo: string | null
  diEtcOtcCode: string | null
}
export function PillResultCard({ drugName, dlCompany, dlMaterial, diClassNo, diEtcOtcCode }: PillResultCardProps) {
  return (
    <div className="mt-4 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
      <p className="mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">약품 정보</p>
      <div className="space-y-2">
        <div>
          <p className="text-xs text-gray-500">약품명</p>
          <p className="text-sm font-medium text-gray-800">{drugName ?? '-'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">제조사</p>
          <p className="text-sm font-medium text-gray-800">{dlCompany ?? '-'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">성분</p>
          <p className="text-sm font-medium text-gray-800">{dlMaterial ?? '-'}</p>
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