import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Pencil, Trash2, MoreVertical, Sparkles, PlusCircle, ImageIcon, ChevronDown, ChevronUp } from 'lucide-react'
import { StatusBadge } from '@/shared/ui/StatusBadge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import { useMedicalRecords, useDeleteRecord, useUpdateRecord, useGenerateGuide } from '@/entities/medical-record/api'
import { useInvalidateGuides } from '@/entities/guide/api'
import { useAddMedication, useMedications, useDrugClassFallback, useScheduleMedication } from '@/entities/medication/api'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'
import type { MedicalRecord, Medication } from '@/entities/medical-record/model'
import { parseDrugName, formatFrequency } from '@/shared/lib/drug-category'
import { toast } from 'sonner'

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

function calcEndDate(startDate: string, days: number | null | undefined, eveningExtra: number): string {
  if (!days) return startDate
  const d = new Date(startDate + 'T00:00:00')
  d.setDate(d.getDate() + days - 1 + eveningExtra)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function fmtDate(iso: string) {
  const [, m, d] = iso.split('-')
  return `${Number(m)}/${Number(d)}`
}

function MedSelectItem({ med, idx, existingMedId, existingDrugClass, alreadyScheduled, isSelected, startDate, eveningExtra, onToggle }: {
  med: Medication; idx: number; existingMedId: string | null; existingDrugClass: string | null; alreadyScheduled: boolean; isSelected: boolean
  startDate: string; eveningExtra: number; onToggle: (i: number) => void
}) {
  const isExisting = !!existingMedId
  const parsed = parseDrugName(med.name ?? '')
  const category = useDrugClassFallback(parsed.name, existingDrugClass ?? med.drug_class, existingMedId ?? undefined)
  const endDate = calcEndDate(startDate, med.days, eveningExtra)

  return (
    <button
      type="button"
      onClick={() => !alreadyScheduled && onToggle(idx)}
      disabled={alreadyScheduled}
      className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors w-full ${
        alreadyScheduled
          ? 'border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed'
          : isExisting
            ? isSelected ? 'border-blue-400 bg-blue-50' : 'border-blue-100 bg-blue-50/50'
            : isSelected ? 'border-[#1D9E75] bg-[#1D9E75]/5' : 'border-gray-100 bg-gray-50'
      }`}
    >
      <div className={`h-4 w-4 shrink-0 rounded border-2 flex items-center justify-center transition-colors ${
        alreadyScheduled
          ? 'border-gray-200 bg-gray-100'
          : isExisting
            ? isSelected ? 'border-blue-400 bg-blue-400' : 'border-blue-200'
            : isSelected ? 'border-[#1D9E75] bg-[#1D9E75]' : 'border-gray-300'
      }`}>
        {alreadyScheduled
          ? <svg className="h-2.5 w-2.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          : isSelected && (
              <svg className="h-2.5 w-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            )
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          {category && (
            <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[#1D9E75]/10 text-[#1D9E75] shrink-0">
              {category}
            </span>
          )}
          <p className="text-xs font-medium text-gray-700 truncate">{parsed.name}</p>
          {alreadyScheduled
            ? <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-400 shrink-0">이미 추가됨</span>
            : isExisting && <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-600 shrink-0">일정 추가</span>
          }
        </div>
        <div className="flex flex-wrap items-center gap-1 mt-1">
          {med.days ? (
            <span className="text-[11px] text-gray-500 font-medium">
              {fmtDate(startDate)} ~ {fmtDate(endDate)}
              <span className="text-gray-400 ml-1">({med.days}일분)</span>
            </span>
          ) : null}
          {(med.dosage != null ? String(med.dosage) : parsed.dosage) && (
            <span className="px-1.5 py-0.5 rounded border border-gray-200 text-[10px] text-gray-500">
              용량 {med.dosage != null ? String(med.dosage) : parsed.dosage}
            </span>
          )}
          {med.frequency && <span className="px-1.5 py-0.5 rounded border border-gray-200 text-[10px] text-gray-500">{med.frequency}회/일</span>}
          {med.instructions && (
            <span className="px-1.5 py-0.5 rounded border border-gray-200 text-[10px] text-gray-500">
              {String(med.instructions)}
            </span>
          )}
          {(() => {
            const times = getScheduledTimes(med.frequency, med.instructions != null ? String(med.instructions) : null)
            const fmt = (t: string) => t.slice(0, 5)
            return (
              <span className="px-1.5 py-0.5 rounded border border-[#1D9E75]/30 bg-[#1D9E75]/5 text-[10px] text-[#1D9E75] font-medium">
                ⏰ {times.map(fmt).join(', ')}
              </span>
            )
          })()}
        </div>
      </div>
    </button>
  )
}

function inferTimeFromInstructions(instructions: string | null | undefined): string {
  if (!instructions) return '08:00:00'
  const s = String(instructions).toLowerCase()
  if (s.includes('취침') || s.includes('자기 전')) return '22:00:00'
  if (s.includes('석식') || s.includes('저녁')) return '18:00:00'
  if (s.includes('중식') || s.includes('점심')) return '12:00:00'
  return '08:00:00'
}

function getScheduledTimes(frequency: number | null | undefined, instructions?: string | null): string[] {
  const freq = frequency != null ? Number(frequency) : null
  const s = instructions ? String(instructions).toLowerCase() : ''

  if (freq === 4) return ['06:00:00', '12:00:00', '18:00:00', '22:00:00']

  if (freq === 3) {
    if (s.includes('취침') || s.includes('자기 전')) return ['08:00:00', '12:00:00', '22:00:00']
    return ['08:00:00', '12:00:00', '18:00:00']
  }

  if (freq === 2) {
    const hasMorning = s.includes('조식') || s.includes('아침')
    const hasLunch  = s.includes('중식') || s.includes('점심')
    const hasEvening = s.includes('석식') || s.includes('저녁')
    const hasBed = s.includes('취침') || s.includes('자기 전')
    if (hasMorning && hasLunch)   return ['08:00:00', '12:00:00']
    if (hasLunch   && hasEvening) return ['12:00:00', '18:00:00']
    if (hasMorning && hasBed)     return ['08:00:00', '22:00:00']
    if (hasEvening && hasBed)     return ['18:00:00', '22:00:00']
    return ['08:00:00', '18:00:00']
  }

  return [inferTimeFromInstructions(instructions)]
}

function AddMedicationsModal({ record, onClose }: { record: MedicalRecord; onClose: () => void }) {
  const meds: Medication[] = record.parsed_data?.medications ?? []
  const { data: existingMeds } = useMedications()
  // drug_name(소문자) → { id, start_date } 맵
  const existingMedMap = new Map((existingMeds ?? []).map((m) => [m.drug_name.trim().toLowerCase(), { id: m.id, start_date: m.start_date ?? null, drug_class: m.drug_class ?? null }]))

  // 시작일: 교부일 or 오늘
  const defaultStart = record.parsed_data?.issued_at
    ? record.parsed_data.issued_at.slice(0, 10)
    : new Date().toISOString().split('T')[0]
  const [startDate, setStartDate] = useState(defaultStart)

  // 저녁 보정: 시작일이 오늘이고 17시 이후면 +1일
  const eveningExtra = (() => {
    const today = new Date().toISOString().split('T')[0]
    return startDate === today && new Date().getHours() >= 17 ? 1 : 0
  })()

  // 이미 일정이 있는 약물은 초기 선택에서 제외
  const [selected, setSelected] = useState<Set<number>>(() => {
    return new Set(
      meds.map((med, i) => {
        const key = parseDrugName(med.name ?? '').name.trim().toLowerCase()
        const existing = existingMedMap.get(key)
        return existing?.start_date ? null : i
      }).filter((i): i is number => i !== null)
    )
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { mutateAsync: addMedication } = useAddMedication()
  const { mutateAsync: scheduleMedication } = useScheduleMedication()

  function toggle(i: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })
  }

  async function handleSubmit() {
    const targets = meds.map((med, i) => ({ med, i })).filter(({ i }) => selected.has(i))
    if (!targets.length) return
    setIsSubmitting(true)
    let successCount = 0
    for (const { med } of targets) {
      try {
        const parsed = parseDrugName(med.name ?? '')
        const existing = existingMedMap.get(parsed.name.trim().toLowerCase()) ?? null
        const existingId = existing?.id ?? null
        const endDate = calcEndDate(startDate, med.days, eveningExtra)
        const times = getScheduledTimes(med.frequency, med.instructions != null ? String(med.instructions) : null)

        if (existingId) {
          if (med.days) {
            for (const t of times) {
              await scheduleMedication({ id: existingId, start_date: startDate, end_date: endDate, scheduled_time: t })
            }
          }
        } else {
          const dosage = parsed.dosage ?? (med.dosage != null ? `${med.dosage}정` : undefined)
          const frequency = formatFrequency(med.frequency != null ? String(med.frequency) : null) ?? undefined
          const instrParts = [
            med.instructions != null ? String(med.instructions) : null,
            med.days != null ? `${med.days}일분` : null,
          ].filter(Boolean)
          const newMed = await addMedication({
            drug_name: parsed.name,
            dosage,
            frequency,
            instructions: instrParts.length ? instrParts.join(' · ') : undefined,
            drug_class: med.drug_class ?? null,
            start_date: startDate,
            end_date: med.days ? endDate : null,
            scheduled_time: times[0],
            record_type: record.record_type === 'prescription' ? 0 : record.record_type === 'medicine_bag' ? 1 : null,
          })
          // 2회/일 이상이면 나머지 시간대 일정 + 알림 추가
          if (newMed && med.days && times.length > 1) {
            for (const t of times.slice(1)) {
              await scheduleMedication({ id: newMed.id, start_date: startDate, end_date: endDate, scheduled_time: t })
            }
          }
        }
        successCount++
      } catch (err: unknown) {
        const axiosErr = err as { response?: { status: number; data?: unknown } }
        const detail = axiosErr?.response?.data
          ? JSON.stringify(axiosErr.response.data)
          : err instanceof Error ? err.message : String(err)
        toast.error(`'${med.name}' 추가 실패: ${detail}`)
      }
    }
    setIsSubmitting(false)
    if (successCount > 0) toast.success(`${successCount}개 처리 완료`)
    if (successCount === 0) return
    onClose()
  }

  const isEvening = eveningExtra > 0

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full sm:max-w-md bg-white rounded-t-3xl sm:rounded-2xl shadow-xl px-6 pt-6 pb-8 flex flex-col gap-4 max-h-[85vh]">
        <div className="flex items-center justify-between shrink-0">
          <div>
            <p className="text-base font-bold text-gray-900">내 의약품에 추가</p>
            <p className="text-xs text-gray-400 mt-0.5">캘린더에 복약 일정을 등록하고 복용 시간 알림을 받을 수 있어요</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 복용 시작일 */}
        <div className="shrink-0 rounded-xl bg-gray-50 border border-gray-100 px-4 py-3 flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-600">복용 시작일</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="text-xs text-gray-700 border border-gray-200 rounded-lg px-2 py-1 bg-white"
            />
          </div>
          {isEvening && (
            <p className="text-[11px] text-amber-600">
              현재 17시 이후로 저녁 복용 시작이 감지되어 종료일을 +1일 적용했습니다.
            </p>
          )}
          {!isEvening && record.parsed_data?.issued_at && (
            <p className="text-[11px] text-gray-400">교부일 기준으로 초기 설정됨</p>
          )}
        </div>

        <div className="flex flex-col gap-2 overflow-y-auto">
          {meds.map((med, i) => {
            const key = parseDrugName(med.name ?? '').name.trim().toLowerCase()
            const existing = existingMedMap.get(key) ?? null
            return (
              <MedSelectItem
                key={i}
                med={med}
                idx={i}
                existingMedId={existing?.id ?? null}
                existingDrugClass={existing?.drug_class ?? null}
                alreadyScheduled={!!existing?.start_date}
                isSelected={selected.has(i)}
                startDate={startDate}
                eveningExtra={eveningExtra}
                onToggle={toggle}
              />
            )
          })}
        </div>

        <div className="flex gap-2 shrink-0">
          <button onClick={onClose} className="flex-1 py-3 rounded-xl text-sm text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors">
            취소
          </button>
          <button
            onClick={handleSubmit}
            disabled={selected.size === 0 || isSubmitting}
            className="flex-1 py-3 rounded-xl text-sm text-white font-semibold disabled:opacity-50 transition-colors"
            style={{ background: '#1D9E75' }}
          >
            {isSubmitting ? '처리 중...' : `${selected.size}개 추가`}
          </button>
        </div>
      </div>
    </div>
  )
}

export function UploadHistoryList() {
  const { data: records, isLoading } = useMedicalRecords()
  const navigate = useNavigate()
  const { mutate: deleteRecord, isPending: isDeleting } = useDeleteRecord()
  const { mutate: updateRecord, isPending: isUpdating } = useUpdateRecord()
  const { mutate: generateGuide, isPending: isGenerating } = useGenerateGuide()
  const invalidateGuides = useInvalidateGuides()
  const [generatingId, setGeneratingId] = useState<string | null>(null)

  const [deleteTarget, setDeleteTarget] = useState<MedicalRecord | null>(null)
  const [editTarget, setEditTarget] = useState<MedicalRecord | null>(null)
  const [editForm, setEditForm] = useState({ hospital: '', pharmacy: '', disease_code: '', issued_at: '' })
  const [editMeds, setEditMeds] = useState<Medication[]>([])
  const [menuOpen, setMenuOpen] = useState<string | null>(null)
  const [addMedTarget, setAddMedTarget] = useState<MedicalRecord | null>(null)
  const [imageOpen, setImageOpen] = useState<string | null>(null)

  function handleGenerateGuide(record: MedicalRecord) {
    setGeneratingId(record.id)
    generateGuide(String(record.id), {
      onSuccess: (data) => {
        invalidateGuides()
        toast.success('가이드 생성 요청 완료!')
        navigate(`/guide?id=${data.guide_id}`)
      },
      onError: () => toast.error('가이드 생성에 실패했습니다.'),
      onSettled: () => setGeneratingId(null),
    })
  }

  function openEdit(record: MedicalRecord) {
    setEditTarget(record)
    setEditForm({
      hospital: record.parsed_data?.hospital ?? '',
      pharmacy: record.parsed_data?.pharmacy ?? '',
      disease_code: record.parsed_data?.disease_code ?? '',
      issued_at: record.parsed_data?.issued_at ?? '',
    })
    setEditMeds(record.parsed_data?.medications ?? [])
  }

  function updateMed(i: number, field: keyof Medication, value: string) {
    setEditMeds(prev => prev.map((m, idx) => {
      if (idx !== i) return m
      if (field === 'days' || field === 'frequency') return { ...m, [field]: value ? Number(value) : null }
      return { ...m, [field]: value || undefined }
    }))
  }

  function removeMed(i: number) {
    setEditMeds(prev => prev.filter((_, idx) => idx !== i))
  }

  function addMed() {
    setEditMeds(prev => [...prev, { name: '' }])
  }

  function handleUpdate() {
    if (!editTarget) return
    updateRecord({
      id: String(editTarget.id),
      parsed_data: {
        ...editTarget.parsed_data,
        medications: editMeds.filter(m => m.name.trim()),
        hospital: editForm.hospital || undefined,
        pharmacy: editForm.pharmacy || undefined,
        disease_code: editForm.disease_code || undefined,
        issued_at: editForm.issued_at || undefined,
      },
    }, { onSuccess: () => setEditTarget(null) })
  }

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
    <>
      <ul className="space-y-3">
        {records.filter(r => r.record_type in TYPE_BADGE).slice(0, 5).map((record) => {
          const meta = RECORD_TYPE_META[record.record_type]
          const canNavigate = record.status === 'completed' && !!record.guide_id
          const canGenerate = record.status === 'completed' && !record.guide_id
          const canAddMeds = record.status === 'completed' && (record.parsed_data?.medications?.length ?? 0) > 0
          const isThisGenerating = generatingId === record.id
          const isMenuOpen = menuOpen === record.id

          const hasImage = !!record.file_url && !record.file_url.endsWith('.pdf')
          const isImageOpen = imageOpen === record.id

          return (
            <li
              key={record.id}
              onClick={() => { setMenuOpen(null); canNavigate && navigate(`/guide?id=${record.guide_id}`) }}
              className={`relative flex flex-col rounded-xl bg-white shadow-sm transition-colors ${canNavigate ? 'cursor-pointer hover:bg-gray-50' : ''}`}
            >
              <div className="flex items-start gap-3 p-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 mt-0.5">
                <RecordIcon name={TYPE_ICON[record.record_type]} />
              </div>

              <div className="flex-1 min-w-0">
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
                      : record.record_type === 'pill_photo'
                        ? record.parsed_data?.medications?.[0]?.name?.split(' ')[0] ?? null
                        : record.parsed_data?.hospital
                    const diseaseName = record.parsed_data?.disease_name
                    return name
                      ? <span className="truncate text-sm font-medium text-gray-800">
                          {name}{diseaseName ? ` (${diseaseName})` : ''}
                        </span>
                      : null
                  })()}
                </div>

                <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                  {(() => {
                    const d = record.parsed_data?.issued_at ? new Date(record.parsed_data.issued_at) : null
                    const valid = d && !isNaN(d.getTime())
                    return valid
                      ? <span className="text-xs text-gray-400">처방일 {d!.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })}</span>
                      : null
                  })()}
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
                    <span className="text-xs text-gray-400">{new Date(record.created_at).toLocaleDateString('ko-KR')}</span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 shrink-0">
                <StatusBadge status={record.status} />

                {canGenerate && !isThisGenerating && (
                  <button
                    className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-white"
                    style={{ background: '#1D9E75' }}
                    onClick={e => { e.stopPropagation(); handleGenerateGuide(record) }}
                    disabled={isThisGenerating || isGenerating}
                  >
                    <Sparkles className="h-3 w-3" />
                    {isThisGenerating ? '생성 중...' : '가이드 생성'}
                  </button>
                )}
                {canAddMeds && (
                  <button
                    className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-[#1D9E75] border border-[#1D9E75]/30 bg-emerald-50 hover:bg-emerald-100 transition-colors"
                    onClick={e => { e.stopPropagation(); setAddMedTarget(record) }}
                  >
                    <PlusCircle className="h-3 w-3" />
                    의약품 추가
                  </button>
                )}

                {/* 더보기 메뉴 */}
                <div className="relative" onClick={e => e.stopPropagation()}>
                  <button
                    className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    onClick={() => setMenuOpen(isMenuOpen ? null : record.id)}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>

                  {isMenuOpen && (
                    <div className="absolute right-0 top-7 z-10 w-28 rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
                      {record.record_type !== 'pill_photo' && (
                        <button
                          className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                          onClick={() => { setMenuOpen(null); openEdit(record) }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                          수정
                        </button>
                      )}
                      <button
                        className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
                        onClick={() => { setMenuOpen(null); setDeleteTarget(record) }}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        삭제
                      </button>
                    </div>
                  )}
                </div>
              </div>
              </div>{/* flex items-start gap-3 p-4 */}

              {hasImage && isImageOpen && (
                <div className="px-4 pb-4" onClick={e => e.stopPropagation()}>
                  <img
                    src={`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}${record.file_url}`}
                    alt="업로드 이미지"
                    className="w-full rounded-lg border border-gray-100 object-contain max-h-72"
                  />
                </div>
              )}

              {hasImage && (
                <button
                  className="flex w-full items-center justify-center gap-1 border-t border-gray-100 py-1.5 text-xs text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition-colors rounded-b-xl"
                  onClick={e => { e.stopPropagation(); setImageOpen(isImageOpen ? null : record.id) }}
                >
                  {isImageOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                  {isImageOpen ? '이미지 접기' : '이미지 보기'}
                </button>
              )}
            </li>
          )
        })}
      </ul>

      {/* 의약품 추가 모달 */}
      {addMedTarget && (
        <AddMedicationsModal record={addMedTarget} onClose={() => setAddMedTarget(null)} />
      )}

      {/* 삭제 확인 다이얼로그 */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="기록을 삭제하시겠어요?"
        description="삭제된 기록과 연결된 가이드도 함께 삭제됩니다. 이 작업은 되돌릴 수 없습니다."
        confirmLabel={isDeleting ? '삭제 중...' : '삭제'}
        variant="danger"
        onConfirm={() => deleteRecord(String(deleteTarget!.id), { onSuccess: () => setDeleteTarget(null) })}
      />

      {/* 수정 다이얼로그 */}
      <Dialog open={!!editTarget} onOpenChange={(open) => !open && setEditTarget(null)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>기록 수정</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {editTarget?.record_type !== 'medicine_bag' ? (
              <label className="block">
                <span className="text-xs text-gray-500">병원명</span>
                <input
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                  value={editForm.hospital}
                  onChange={e => setEditForm(f => ({ ...f, hospital: e.target.value }))}
                />
              </label>
            ) : (
              <label className="block">
                <span className="text-xs text-gray-500">약국명</span>
                <input
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                  value={editForm.pharmacy}
                  onChange={e => setEditForm(f => ({ ...f, pharmacy: e.target.value }))}
                />
              </label>
            )}
            <label className="block">
              <span className="text-xs text-gray-500">질병 분류 기호</span>
              <input
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                placeholder="예: N30.0"
                value={editForm.disease_code}
                onChange={e => setEditForm(f => ({ ...f, disease_code: e.target.value }))}
              />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">처방일</span>
              <input
                type="date"
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500"
                value={editForm.issued_at ? editForm.issued_at.slice(0, 10) : ''}
                onChange={e => setEditForm(f => ({ ...f, issued_at: e.target.value }))}
              />
            </label>

            {/* 약물 목록 */}
            <div className="pt-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">약물 목록</span>
                <button
                  type="button"
                  onClick={addMed}
                  className="flex items-center gap-1 text-xs font-semibold text-[#1D9E75] hover:opacity-75 transition-opacity"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                  </svg>
                  약물 추가
                </button>
              </div>
              <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-0.5">
                {editMeds.length === 0 ? (
                  <p className="text-xs text-gray-400 py-2 text-center">등록된 약물이 없습니다.</p>
                ) : (
                  editMeds.map((med, i) => (
                    <div key={i} className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5 flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <input
                          className="flex-1 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs outline-none focus:border-green-500"
                          placeholder="약품명"
                          value={med.name}
                          onChange={e => updateMed(i, 'name', e.target.value)}
                        />
                        <button
                          type="button"
                          onClick={() => removeMed(i)}
                          className="shrink-0 p-1.5 rounded-md text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors"
                        >
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <label className="flex flex-col gap-0.5">
                          <span className="text-[10px] text-gray-400">용량</span>
                          <input
                            className="w-full rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs outline-none focus:border-green-500"
                            placeholder="예: 1정"
                            value={med.dosage ?? ''}
                            onChange={e => updateMed(i, 'dosage', e.target.value)}
                          />
                        </label>
                        <label className="flex flex-col gap-0.5">
                          <span className="text-[10px] text-gray-400">1일 횟수</span>
                          <input
                            className="w-full rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs outline-none focus:border-green-500"
                            placeholder="예: 3"
                            type="number"
                            min="1"
                            max="10"
                            value={med.frequency ?? ''}
                            onChange={e => updateMed(i, 'frequency', e.target.value)}
                            onKeyDown={e => ['-', '+', 'e'].includes(e.key) && e.preventDefault()}
                          />
                        </label>
                        <label className="flex flex-col gap-0.5">
                          <span className="text-[10px] text-gray-400">복용 일수</span>
                          <input
                            className="w-full rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs outline-none focus:border-green-500"
                            placeholder="예: 3"
                            type="number"
                            min="1"
                            value={med.days ?? ''}
                            onChange={e => updateMed(i, 'days', e.target.value)}
                            onKeyDown={e => ['-', '+', 'e'].includes(e.key) && e.preventDefault()}
                          />
                        </label>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditTarget(null)}>취소</Button>
            <Button disabled={isUpdating} onClick={handleUpdate}>
              {isUpdating ? '저장 중...' : '저장'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
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
      <>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="m8.5 8.5 7 7" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2}
          d="M 15.5 5 A 3 3 0 0 1 19 8.5" />
      </>
    ),
  }
  return (
    <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      {paths[name]}
    </svg>
  )
}
