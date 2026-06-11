// frontend/src/features/record-upload/PillResultCard.tsx
import { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { usePillMatchOcr } from '@/entities/medical-record/api'
import type { PillResult } from '@/entities/medical-record/model'

interface PillResultCardProps {
  pillResult: PillResult
  onRematch: (result: PillResult) => void
}

export function PillResultCard({ pillResult, onRematch }: PillResultCardProps) {
  const initialTokens = pillResult.ocr_texts.length > 0
    ? pillResult.ocr_texts
    : [pillResult.print_front, pillResult.print_back].filter((t): t is string => !!t)

  const [tokens, setTokens] = useState<string[]>(initialTokens)
  const [input, setInput] = useState('')

  const { mutate: matchOcr, isPending } = usePillMatchOcr()

  function addToken() {
    const trimmed = input.trim().toUpperCase()
    if (trimmed && !tokens.includes(trimmed)) {
      setTokens((prev) => [...prev, trimmed])
    }
    setInput('')
  }

  function removeToken(token: string) {
    setTokens((prev) => prev.filter((t) => t !== token))
  }

  function handleRematch() {
    matchOcr(tokens, {
      onSuccess: (data) => onRematch(data),
    })
  }

  const colorLabel = [pillResult.color_class1, pillResult.color_class2]
    .filter(Boolean)
    .join(' / ')

  return (
    <div className="space-y-4">
      {/* OCR 식별코드 확인/수정 */}
      <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <p className="mb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide">OCR 식별코드 확인</p>
        <p className="mb-3 text-xs text-gray-400">잘못 인식된 텍스트는 삭제하고, 반대면 식별코드가 있다면 추가하면 정확도가 올라가요.</p>
        <div className="flex flex-wrap gap-2 mb-3">
          {tokens.map((token) => (
            <span key={token} className="flex items-center gap-1 rounded-md bg-gray-100 px-3 py-1 text-sm text-gray-700">
              {token}
              <button type="button" onClick={() => removeToken(token)} className="text-gray-400 hover:text-gray-600">
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addToken()}
            placeholder="식별코드 입력 (예: ER)"
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-primary"
          />
          <button
            type="button"
            onClick={addToken}
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            추가
          </button>
        </div>
      </div>

      {/* 약품 정보 */}
      <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <p className="mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">약품 정보</p>
        <div className="space-y-2">
          <div>
            <p className="text-xs text-gray-500">약품명</p>
            <p className="text-sm font-medium text-gray-800">{pillResult.drug_name ?? '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">제조사</p>
            <p className="text-sm font-medium text-gray-800">{pillResult.dl_company ?? '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">성분</p>
            <p className="text-sm font-medium text-gray-800">{pillResult.dl_material ?? '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">효능/효과</p>
            <p className="text-sm font-medium text-gray-800">{pillResult.di_class_no ?? '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">구분</p>
            <p className="text-sm font-medium text-gray-800">{pillResult.di_etc_otc_code ?? '-'}</p>
          </div>
          {(pillResult.color_class1 || pillResult.drug_shape || pillResult.chart) && (
            <>
              <div>
                <p className="text-xs text-gray-500">색상</p>
                <p className="text-sm font-medium text-gray-800">{colorLabel || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">모양</p>
                <p className="text-sm font-medium text-gray-800">{pillResult.drug_shape ?? '-'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">제형</p>
                <p className="text-sm font-medium text-gray-800">{pillResult.chart ?? '-'}</p>
              </div>
            </>
          )}
        </div>
        <p className="mt-3 text-xs text-gray-400">약품 정보가 맞지 않으면 식별코드를 수정 후 재매칭하세요.</p>
        <Button
          variant="outline"
          className="mt-2 w-full"
          disabled={isPending || tokens.length === 0}
          onClick={handleRematch}
        >
          {isPending ? '매칭 중...' : '재매칭'}
        </Button>
      </div>
    </div>
  )
}