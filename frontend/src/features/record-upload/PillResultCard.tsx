// frontend/src/features/record-upload/PillResultCard.tsx
import { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { usePillMatchOcr } from '@/entities/medical-record/api'
import type { CandidateResult, PillResult } from '@/entities/medical-record/model'

interface EditableTokenProps {
  value: string
  onChange: (v: string) => void
  onRemove: () => void
}

function EditableToken({ value, onChange, onRemove }: EditableTokenProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)

  function commit() {
    const trimmed = draft.trim().toUpperCase()
    if (trimmed) onChange(trimmed)
    else onRemove()
    setEditing(false)
  }

  if (editing) {
    return (
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === 'Enter' && commit()}
        className="rounded-md border border-primary px-3 py-1 text-sm outline-none w-24"
      />
    )
  }

  return (
    <span className="flex items-center gap-1 rounded-md bg-gray-100 px-3 py-1 text-sm text-gray-700">
      <button type="button" onClick={() => { setDraft(value); setEditing(true) }} className="hover:text-primary">
        {value}
      </button>
      <button type="button" onClick={onRemove} className="text-gray-400 hover:text-gray-600">
        <X size={12} />
      </button>
    </span>
  )
}

interface CandidateCardProps {
  candidate: CandidateResult
  selected: boolean
  onSelect: () => void
}

function CandidateCard({ candidate, selected, onSelect }: CandidateCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left rounded-lg border p-3 transition-colors ${
        selected
          ? 'border-primary bg-primary/5'
          : 'border-gray-200 bg-white hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium truncate ${selected ? 'text-primary' : 'text-gray-800'}`}>
            {candidate.drug_name}
          </p>
          <div className="flex flex-wrap gap-1 mt-1">
            {candidate.color_class1 && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {candidate.color_class1}
              </span>
            )}
            {candidate.drug_shape && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {candidate.drug_shape}
              </span>
            )}
            {candidate.di_etc_otc_code && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {candidate.di_etc_otc_code}
              </span>
            )}
          </div>
        </div>
        <div className={`mt-0.5 w-4 h-4 rounded-full border-2 flex-shrink-0 ${
          selected ? 'border-primary bg-primary' : 'border-gray-300'
        }`} />
      </div>
    </button>
  )
}

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
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateResult | null>(
    pillResult.candidates ? pillResult.candidates[0] : null
  )

  const { mutate: matchOcr, isPending } = usePillMatchOcr()

  const candidates = pillResult.candidates ?? []
  const hasMultipleCandidates = candidates.length > 1

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
      onSuccess: (data) => {
        setSelectedCandidate(data.candidates ? data.candidates[0] : null)
        onRematch(data)
      },
    })
  }

  function handleConfirmCandidate() {
    if (!selectedCandidate) return
    const confirmed: PillResult = {
      ...pillResult,
      drug_name: selectedCandidate.drug_name,
      dl_material: selectedCandidate.dl_material,
      di_class_no: selectedCandidate.di_class_no,
      di_etc_otc_code: selectedCandidate.di_etc_otc_code,
      print_front: selectedCandidate.print_front,
      print_back: selectedCandidate.print_back,
      color_class1: selectedCandidate.color_class1,
      drug_shape: selectedCandidate.drug_shape,
      chart: selectedCandidate.chart,
      dl_company: selectedCandidate.dl_company,
      candidates: null,
    }
    onRematch(confirmed)
  }

  const displayResult = selectedCandidate && !hasMultipleCandidates
    ? { ...pillResult, ...selectedCandidate }
    : pillResult

  const colorLabel = [displayResult.color_class1, pillResult.color_class2]
    .filter(Boolean)
    .join(' / ')

  return (
    <div className="space-y-4">
      {/* OCR 식별코드 확인/수정 */}
      <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <p className="mb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide">OCR 식별코드 확인</p>
        <p className="mb-3 text-xs text-gray-400">태그를 눌러 수정하거나 삭제하고, 반대면 식별코드가 있다면 추가하면 정확도를 높일 수 있습니다.</p>
        <div className="flex flex-wrap gap-2 mb-3">
          {tokens.map((token, idx) => (
            <EditableToken
              key={idx}
              value={token}
              onChange={(newVal) => {
                setTokens((prev) => prev.map((t, i) => (i === idx ? newVal : t)))
              }}
              onRemove={() => removeToken(token)}
            />
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

      {/* 복수 후보 선택 */}
      {hasMultipleCandidates && (
        <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <p className="mb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide">후보 약품 선택</p>
          <p className="mb-3 text-xs text-gray-400">업로드한 약과 색상·모양이 일치하는 항목을 선택하세요.</p>
          <div className="space-y-2">
            {candidates.map((c) => (
              <CandidateCard
                key={c.kcode}
                candidate={c}
                selected={selectedCandidate?.kcode === c.kcode}
                onSelect={() => setSelectedCandidate(c)}
              />
            ))}
          </div>
          <Button
            className="mt-3 w-full"
            disabled={!selectedCandidate}
            onClick={handleConfirmCandidate}
          >
            이 약품으로 확정
          </Button>
        </div>
      )}

      {/* 약품 정보 */}
      <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <p className="mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">약품 정보</p>
        <div className="space-y-2">
          <div>
            <p className="text-xs text-gray-500">약품명</p>
            <p className="text-sm font-medium text-gray-800">{displayResult.drug_name || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">제조사</p>
            <p className="text-sm font-medium text-gray-800">{displayResult.dl_company || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">성분</p>
            <p className="text-sm font-medium text-gray-800">{displayResult.dl_material || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">효능/효과</p>
            <p className="text-sm font-medium text-gray-800">{displayResult.di_class_no || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">구분</p>
            <p className="text-sm font-medium text-gray-800">{displayResult.di_etc_otc_code || '-'}</p>
          </div>
          {(displayResult.color_class1 || displayResult.drug_shape || displayResult.chart) && (
            <>
              <div>
                <p className="text-xs text-gray-500">색상</p>
                <p className="text-sm font-medium text-gray-800">{colorLabel || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">모양</p>
                <p className="text-sm font-medium text-gray-800">{displayResult.drug_shape || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">제형</p>
                <p className="text-sm font-medium text-gray-800">{displayResult.chart || '-'}</p>
              </div>
            </>
          )}
        </div>
        <p className="mt-3 text-xs text-gray-400">약품 정보(색상, 모양)가 내가 올린 알약 이미지와 다르다면 식별코드를 수정 후 재매칭하세요.</p>
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