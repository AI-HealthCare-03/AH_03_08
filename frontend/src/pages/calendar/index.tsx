import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { toast } from '@/shared/lib/toast'
import { Pencil } from 'lucide-react'
import { PageHeader } from '@/shared/ui/PageHeader'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useMonthlyCalendar, useUpdateEventStatus, useDeleteCalendarEvent, useCreateCalendarEvent, useUpdateEventTime } from '@/entities/calendar/api'
import {
  useMedications, useAddMedication, useUpdateMedication, useDeleteMedication,
  useDrugClassFallback, useDrugSearch,
} from '@/entities/medication/api'
import type { CalendarEvent } from '@/entities/calendar/model'
import type { MedicationItem } from '@/entities/medication/model'

const STATUS_CONFIG = {
  TAKEN:   { label: '복용 완료', active: 'bg-emerald-100 text-emerald-600', dot: 'bg-emerald-400', text: 'text-emerald-600' },
  MISSED:  { label: '미복용',   active: 'bg-red-100 text-red-500',         dot: 'bg-red-400',     text: 'text-red-500'    },
  PENDING: { label: '예정',     active: 'bg-gray-100 text-gray-500',       dot: 'bg-gray-300',    text: 'text-gray-400'   },
}

// 왼쪽=미복용(빨강) · 중간=예정(회색) · 오른쪽=복용완료(초록)
const STATUS_ORDER = ['MISSED', 'PENDING', 'TAKEN'] as const

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

const SOURCE_BADGE: Record<number, { label: string; bg: string; color: string }> = {
  0: { label: '처방전', bg: '#EFF6FF', color: '#1D4ED8' },
  1: { label: '약봉투', bg: '#FFF7ED', color: '#C2410C' },
}

const DOSAGE_UNITS      = ['mg', 'g', 'ml', 'mcg', 'IU', '정', '캡슐', '포']
const FREQUENCY_OPTIONS = ['하루 1회', '하루 2회', '하루 3회', '하루 4회', '필요시 복용']
const INSTRUCTION_OPTIONS = ['식전 30분', '식후 30분', '식후 즉시', '취침 전', '공복']
const INPUT_CLS = 'rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10 w-full'

function formatTime(time: string): string {
  const [hourStr, minuteStr] = time.split(':')
  const hour = parseInt(hourStr, 10)
  const ampm = hour < 12 ? '오전' : '오후'
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
  return `${ampm} ${String(displayHour).padStart(2, '0')}:${minuteStr}`
}

function timeSlotLabel(time: string): '아침' | '점심' | '오후' | '저녁' | '밤' {
  const hour = parseInt(time.split(':')[0], 10)
  if (hour >= 5 && hour < 10) return '아침'
  if (hour >= 10 && hour < 14) return '점심'
  if (hour >= 14 && hour < 18) return '오후'
  if (hour >= 18 && hour < 22) return '저녁'
  return '밤'
}

const SLOT_STYLE = {
  아침: 'bg-amber-50 text-amber-600',
  점심: 'bg-sky-50 text-sky-600',
  오후: 'bg-orange-50 text-orange-600',
  저녁: 'bg-indigo-50 text-indigo-600',
  밤:   'bg-violet-50 text-violet-600',
} as const

function parseDosage(dosage: string | null): { num: string; unit: string } {
  if (!dosage) return { num: '', unit: 'mg' }
  const match = dosage.match(/^([\d.]+)(.+)$/)
  if (match) return { num: match[1], unit: DOSAGE_UNITS.includes(match[2]) ? match[2] : 'mg' }
  return { num: '', unit: 'mg' }
}

function OptionGroup({ options, value, onChange, allowDeselect = true }: {
  options: string[]; value: string; onChange: (v: string) => void; allowDeselect?: boolean
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => (
        <button key={opt} type="button"
          onClick={() => onChange(allowDeselect && opt === value ? '' : opt)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
            value === opt ? 'border-[#1D9E75] bg-[#1D9E75]/10 text-[#1D9E75]' : 'border-gray-200 text-gray-500 hover:bg-gray-50'
          }`}>
          {opt}
        </button>
      ))}
    </div>
  )
}

function BottomSheet({ onClose, title, children }: { onClose: () => void; title: string; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full sm:max-w-md bg-white rounded-t-3xl sm:rounded-2xl shadow-xl flex flex-col">
        <div className="flex items-center justify-between px-6 pt-6 pb-4 shrink-0 border-b border-gray-50">
          <p className="text-base font-bold text-gray-900">{title}</p>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors">
            <XIcon />
          </button>
        </div>
        <div className="px-6 pb-8" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          <div className="flex flex-col gap-5 pt-4">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── 의약품 등록 / 수정 모달 ──────────────────────────────────────────────────

function MedicationModal({ onClose, editItem }: { onClose: () => void; editItem?: MedicationItem }) {
  const isEdit = !!editItem
  const parsed = parseDosage(editItem?.dosage ?? null)
  const [drugName, setDrugName] = useState(editItem?.drug_name ?? '')
  const [drugClass, setDrugClass] = useState(editItem?.drug_class ?? '')
  const [dosageNum, setDosageNum] = useState(parsed.num)
  const [dosageUnit, setDosageUnit] = useState(parsed.unit)
  const [frequency, setFrequency] = useState(editItem?.frequency ?? '')
  const [instructions, setInstructions] = useState(editItem?.instructions ?? '')
  const [startDate, setStartDate] = useState(() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` })
  const [endDate, setEndDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('08:00')
  // 수정 모드: 빈값이면 시간 변경 없음
  const [newTime, setNewTime] = useState('')
  const [memo, setMemo] = useState(editItem?.memo ?? '')
  const [searchQuery, setSearchQuery] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { mutate: add, isPending: isAdding } = useAddMedication()
  const { mutate: update, isPending: isUpdating } = useUpdateMedication()
  const isPending = isAdding || isUpdating

  const { data: searchResults, isFetching: isSearching } = useDrugSearch(searchQuery)

  function handleSearch() {
    if (drugName.trim().length < 2) return
    setSearchQuery(drugName.trim())
    setShowDropdown(true)
  }

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleSelectDrug = useCallback((name: string, cls: string | null) => {
    setDrugName(name)
    setDrugClass(cls ?? '')
    setShowDropdown(false)
  }, [])

  function handleSubmit() {
    if (!drugName.trim()) return
    const dosage = dosageNum.trim() ? `${dosageNum.trim()}${dosageUnit}` : undefined
    if (isEdit) {
      update(
        {
          id: editItem!.id,
          drug_name: drugName.trim(),
          dosage,
          frequency: frequency || undefined,
          instructions: instructions || undefined,
          drug_class: drugClass || null,
          memo: memo || null,
          ...(newTime ? { scheduled_time: `${newTime}:00` } : {}),
        },
        { onSuccess: onClose },
      )
    } else {
      add(
        {
          drug_name: drugName.trim(),
          dosage,
          frequency: frequency || undefined,
          instructions: instructions || undefined,
          drug_class: drugClass || null,
          memo: memo || null,
          start_date: startDate || null,
          end_date: endDate || null,
          scheduled_time: endDate ? `${scheduledTime}:00` : null,
        },
        { onSuccess: onClose },
      )
    }
  }

  return (
    <BottomSheet onClose={onClose} title={isEdit ? '의약품 수정' : '의약품 등록'}>
      <div className="flex flex-col gap-4">
        {/* 약품명 */}
        <div className="relative flex flex-col gap-1.5" ref={dropdownRef}>
          <label className="text-xs font-semibold text-gray-500">약품명 <span className="text-red-400">*</span></label>
          <div className="relative">
            <input
              type="text"
              value={drugName}
              onChange={(e) => { setDrugName(e.target.value); setDrugClass('') }}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="예: 타이레놀"
              autoFocus
              className={INPUT_CLS + ' pr-10'}
            />
            <button
              type="button"
              onClick={handleSearch}
              disabled={drugName.trim().length < 2 || isSearching}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-[#1D9E75] hover:bg-emerald-50 transition-colors disabled:opacity-40"
            >
              {isSearching ? (
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                </svg>
              )}
            </button>
            {showDropdown && searchResults && searchResults.length > 0 && (
              <div className="absolute z-10 top-full mt-1 w-full bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden">
                {searchResults.map((item, i) => (
                  <button key={i} type="button"
                    onMouseDown={() => handleSelectDrug(item.drug_name, item.drug_class)}
                    className="w-full flex flex-col gap-0.5 px-3 py-2.5 text-left hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0">
                    <span className="text-sm text-gray-800 font-medium">{item.drug_name}</span>
                    {item.drug_class && <span className="text-xs text-[#1D9E75]">{item.drug_class}</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
          {drugClass && <p className="text-xs text-[#1D9E75] font-medium">약효분류: {drugClass}</p>}
        </div>

        {/* 용량 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">용량</label>
          <input type="number" step="any" value={dosageNum} onChange={(e) => setDosageNum(e.target.value)}
            placeholder="예: 500" className={INPUT_CLS} />
          <OptionGroup options={DOSAGE_UNITS} value={dosageUnit} onChange={setDosageUnit} allowDeselect={false} />
        </div>

        {/* 복용 횟수 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">복용 횟수</label>
          <OptionGroup options={FREQUENCY_OPTIONS} value={frequency} onChange={setFrequency} />
        </div>

        {/* 복용 시기 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">복용 시기</label>
          <OptionGroup options={INSTRUCTION_OPTIONS} value={instructions} onChange={setInstructions} />
        </div>

        {/* 등록 전용: 복용 기간 + 시간 */}
        {!isEdit && (
          <>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-gray-500">복용 기간</label>
              <div className="flex items-center gap-2">
                <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
                  className={INPUT_CLS + ' flex-1'} />
                <span className="text-gray-400 text-sm shrink-0">~</span>
                <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
                  className={INPUT_CLS + ' flex-1'} />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-gray-500">복용 시간</label>
              <input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)}
                className={INPUT_CLS} />
            </div>
          </>
        )}

        {/* 메모 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">메모</label>
          <textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            placeholder="복용 관련 메모를 입력하세요"
            rows={2}
            className={INPUT_CLS + ' resize-none'}
          />
        </div>

        {/* 수정 전용: 시간 변경 (선택) */}
        {isEdit && (
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-500">
              복용 시간 변경
              <span className="ml-1.5 font-normal text-gray-400">· 변경할 경우에만 입력하세요</span>
            </label>
            <input type="time" value={newTime} onChange={(e) => setNewTime(e.target.value)}
              className={INPUT_CLS} />
            {newTime && (
              <p className="text-xs text-amber-600">미래 PENDING 일정과 알림 시간이 모두 {formatTime(`${newTime}:00`)}으로 변경됩니다.</p>
            )}
          </div>
        )}
      </div>

      <div className="flex gap-2 pt-2">
        <button onClick={onClose}
          className="flex-1 py-3 rounded-xl text-sm text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors">
          취소
        </button>
        <button onClick={handleSubmit} disabled={!drugName.trim() || isPending}
          className="flex-1 py-3 rounded-xl text-sm text-white font-semibold disabled:opacity-50 transition-colors"
          style={{ background: '#1D9E75' }}>
          {isPending ? '저장 중...' : isEdit ? '저장' : '등록'}
        </button>
      </div>
    </BottomSheet>
  )
}

// ─── 시간별 이벤트 행 ────────────────────────────────────────────────────────

function TimeSlotEventRow({ item, medication }: { item: CalendarEvent; medication?: MedicationItem }) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { mutate: updateStatus, isPending: isUpdating } = useUpdateEventStatus()
  const { mutate: remove, isPending: isDeleting } = useDeleteCalendarEvent()
  const category = useDrugClassFallback(medication?.drug_name ?? '', medication?.drug_class, medication?.id)
  const displayCategory = category
  const sourceBadge = medication?.record_type != null ? (SOURCE_BADGE[medication.record_type] ?? null) : null

  const statusIdx = STATUS_ORDER.indexOf(item.status as typeof STATUS_ORDER[number])
  function handleCycle() {
    updateStatus({ id: item.id, status: STATUS_ORDER[(statusIdx + 1) % STATUS_ORDER.length] })
  }

  return (
    <div className="flex items-center gap-3 px-4 py-3 border-t border-gray-50">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          {displayCategory && (
            <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[#1D9E75]/10 text-[#1D9E75] shrink-0">
              {displayCategory}
            </span>
          )}
          <p className="text-sm font-medium text-gray-700 truncate">{medication?.drug_name ?? '알 수 없음'}</p>
        </div>
        {(sourceBadge || medication?.source_name || medication?.diagnosis) && (
          <div className="flex items-center gap-1 mt-0.5 flex-wrap">
            {sourceBadge && (
              <span className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold"
                style={{ background: sourceBadge.bg, color: sourceBadge.color }}>
                {sourceBadge.label}
              </span>
            )}
            {medication?.source_name && <span className="text-xs text-gray-500 truncate">{medication.source_name}</span>}
            {medication?.diagnosis && (
              <>
                {medication.source_name && <span className="text-gray-300 text-xs">·</span>}
                <span className="text-xs text-gray-400 truncate">{medication.diagnosis}</span>
              </>
            )}
          </div>
        )}
        {item.note && <p className="text-xs text-gray-400 mt-0.5 truncate">{item.note}</p>}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className={`text-xs font-medium w-14 text-right transition-colors ${STATUS_CONFIG[item.status].text}`}>
          {STATUS_CONFIG[item.status].label}
        </span>
        <button
          onClick={handleCycle}
          disabled={isUpdating}
          className="relative w-16 h-6 shrink-0 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
        >
          <div className="absolute top-1/2 inset-x-0 h-0.5 bg-gray-200 -translate-y-1/2 rounded-full" />
          <div
            className={`absolute w-5 h-5 rounded-full shadow-md transition-all duration-200 pointer-events-none ${STATUS_CONFIG[item.status].dot}`}
            style={{ top: '50%', left: 0, transform: `translate(${statusIdx * 22}px, -50%)` }}
          />
        </button>
        <button
          onClick={() => setDeleteOpen(true)}
          disabled={isDeleting}
          className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-50 transition-colors disabled:opacity-40"
        >
          <TrashIcon />
        </button>
      </div>
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="일정을 삭제하시겠습니까?"
        description="삭제된 일정은 복구할 수 없습니다."
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => remove(item.id)}
      />
    </div>
  )
}

// ─── 시간별 그룹 ─────────────────────────────────────────────────────────────


function TimeSlotGroup({ time, events, medMap }: { time: string; events: CalendarEvent[]; medMap: Record<string, MedicationItem> }) {
  const label = timeSlotLabel(time)
  const [editing, setEditing] = useState(false)
  const [newTime, setNewTime] = useState(time.slice(0, 5))
  const { mutateAsync: updateTime, isPending: isTimePending } = useUpdateEventTime()
  const { mutate: updateStatus, isPending: isStatusPending } = useUpdateEventStatus()

  const groupStatus = events.every(ev => ev.status === events[0].status) ? events[0].status : null

  async function handleConfirm() {
    const formatted = `${newTime}:00`
    await Promise.all(events.map((ev) => updateTime({ id: ev.id, scheduled_time: formatted })))
    setEditing(false)
  }

  function handleBatchStatus(s: typeof STATUS_ORDER[number]) {
    events.forEach((ev) => { if (ev.status !== s) updateStatus({ id: ev.id, status: s }) })
  }

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 bg-gray-50/70">
        {editing ? (
          <div className="flex items-center gap-2 flex-1" onClick={(e) => e.stopPropagation()}>
            <input
              type="time"
              value={newTime}
              onChange={(e) => setNewTime(e.target.value)}
              className="rounded-md border border-gray-200 px-2 py-0.5 text-sm font-bold text-gray-700 outline-none focus:border-[#1D9E75]"
            />
            <button
              onClick={handleConfirm}
              disabled={isTimePending}
              className="text-xs font-semibold text-white px-2 py-0.5 rounded-md"
              style={{ background: '#1D9E75' }}
            >
              {isTimePending ? '저장 중' : '확인'}
            </button>
            <button
              onClick={() => { setEditing(false); setNewTime(time.slice(0, 5)) }}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              취소
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-1">
              <span className="text-sm font-bold text-gray-700">{formatTime(time)}</span>
              <button
                onClick={() => setEditing(true)}
                className="p-1 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-200/60 transition-colors"
                title="시간 일괄 변경"
              >
                <Pencil className="h-5 w-5" />
              </button>
            </div>
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${SLOT_STYLE[label]}`}>{label}</span>
            <div className="ml-auto inline-flex shrink-0 rounded-lg border border-gray-200 bg-gray-50 p-0.5 gap-0.5">
              {(['MISSED', 'PENDING', 'TAKEN'] as const).map((s) => (
                <button
                  key={s}
                  disabled={isStatusPending}
                  onClick={() => handleBatchStatus(s)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all disabled:opacity-50 ${
                    groupStatus === s ? STATUS_CONFIG[s].active + ' shadow-sm' : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  {STATUS_CONFIG[s].label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
      {events.map((ev) => <TimeSlotEventRow key={ev.id} item={ev} medication={medMap[ev.medication_id]} />)}
    </div>
  )
}

// ─── 의약품 목록 바텀시트 ────────────────────────────────────────────────────

function MedicationListItem({ medication }: { medication: MedicationItem }) {
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { mutate: remove, isPending: isDeleting } = useDeleteMedication()
  const category = useDrugClassFallback(medication.drug_name, medication.drug_class, medication.id)
  const displayCategory = category
  const sourceBadge = medication.record_type != null ? (SOURCE_BADGE[medication.record_type] ?? null) : null

  return (
    <>
      <div className="flex items-center gap-3 py-3 border-b border-gray-50 last:border-0">
        <div className="h-9 w-9 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
          <PillIcon />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            {displayCategory && (
              <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[#1D9E75]/10 text-[#1D9E75] shrink-0">
                {displayCategory}
              </span>
            )}
            <p className="text-sm font-medium text-gray-800 truncate">{medication.drug_name}</p>
          </div>
          <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
            {sourceBadge && (
              <span className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold"
                style={{ background: sourceBadge.bg, color: sourceBadge.color }}>
                {sourceBadge.label}
              </span>
            )}
            {medication.source_name && (
              <span className="text-xs text-gray-500 truncate">{medication.source_name}</span>
            )}
            {medication.start_date && (
              <span className="text-xs text-gray-400">복용 시작 {medication.start_date}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-0.5 shrink-0">
          <button onClick={() => setEditOpen(true)}
            className="p-2 rounded-lg text-gray-400 hover:text-[#1D9E75] hover:bg-emerald-50 transition-colors">
            <EditIcon />
          </button>
          <button onClick={() => setDeleteOpen(true)} disabled={isDeleting}
            className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-50 transition-colors disabled:opacity-40">
            <TrashIcon />
          </button>
        </div>
      </div>

      {editOpen && <MedicationModal editItem={medication} onClose={() => setEditOpen(false)} />}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={`'${medication.drug_name}'을 삭제하시겠습니까?`}
        description="의약품을 삭제하면 연결된 알림과 복약 일정도 함께 삭제됩니다."
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => remove(medication.id)}
      />
    </>
  )
}

function MedicationListSheet({ onClose }: { onClose: () => void }) {
  const { data: medications } = useMedications()
  const sorted = [...(medications ?? [])].sort((a, b) => {
    const da = a.start_date ?? a.created_at
    const db = b.start_date ?? b.created_at
    return da > db ? -1 : da < db ? 1 : 0
  })

  return (
    <BottomSheet onClose={onClose} title="의약품 목록">
      {!sorted.length ? (
        <div className="py-8 flex flex-col items-center gap-2">
          <p className="text-sm text-gray-400">등록된 의약품이 없습니다.</p>
        </div>
      ) : (
        <div className="flex flex-col">
          {sorted.map((med) => (
            <MedicationListItem key={med.id} medication={med} />
          ))}
        </div>
      )}
    </BottomSheet>
  )
}

// ─── 날짜별 일정 추가 모달 ───────────────────────────────────────────────────

function CalendarEventAddModal({ defaultDate, onClose }: { defaultDate: string; onClose: () => void }) {
  const { data: medications } = useMedications()
  const [medicationId, setMedicationId] = useState('')
  const [time, setTime] = useState('08:00')
  const [note, setNote] = useState('')
  const { mutate: create, isPending } = useCreateCalendarEvent()

  function handleSubmit() {
    if (!medicationId) return
    create(
      { medication_id: medicationId, event_date: defaultDate, scheduled_time: `${time}:00`, note: note || undefined },
      {
        onSuccess: onClose,
        onError: (error: unknown) => {
          const status = (error as { response?: { status?: number } })?.response?.status
          if (status === 409) {
            toast.error('이미 같은 시간에 해당 약의 복약 일정이 존재합니다.')
          } else {
            toast.error('일정 추가에 실패했습니다. 다시 시도해주세요.')
          }
        },
      },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full sm:max-w-md bg-white rounded-t-3xl sm:rounded-2xl shadow-xl px-6 pt-6 pb-8 flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <p className="text-base font-bold text-gray-900">복약 일정 추가</p>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors">
            <XIcon />
          </button>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-500">날짜</label>
            <div className="rounded-xl border border-gray-100 bg-gray-50 px-3 py-2.5 text-sm text-gray-500">
              {defaultDate.replace(/-/g, '. ')}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-500">의약품 <span className="text-red-400">*</span></label>
            {!medications?.length ? (
              <p className="text-xs text-gray-400">등록된 의약품이 없습니다.</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {medications.map((med) => (
                  <button key={med.id} type="button"
                    onClick={() => setMedicationId(med.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      medicationId === med.id
                        ? 'border-[#1D9E75] bg-[#1D9E75]/10 text-[#1D9E75]'
                        : 'border-gray-200 text-gray-500 hover:bg-gray-50'
                    }`}>
                    {med.drug_name}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-500">복약 시간</label>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className={INPUT_CLS} />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-500">메모 <span className="font-normal text-gray-400">(선택)</span></label>
            <input type="text" value={note} onChange={(e) => setNote(e.target.value)}
              placeholder="예: 식후 30분" className={INPUT_CLS} />
          </div>
        </div>

        <div className="flex gap-2">
          <button onClick={onClose}
            className="flex-1 py-3 rounded-xl text-sm text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors">
            취소
          </button>
          <button onClick={handleSubmit} disabled={!medicationId || isPending}
            className="flex-1 py-3 rounded-xl text-sm text-white font-semibold disabled:opacity-50 transition-colors"
            style={{ background: '#1D9E75' }}>
            {isPending ? '저장 중...' : '추가'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── 페이지 ──────────────────────────────────────────────────────────────────

export function CalendarPage() {
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [selectedDate, setSelectedDate] = useState(todayStr)
  const [addEventOpen, setAddEventOpen] = useState(false)
  const [addMedOpen, setAddMedOpen] = useState(false)
  const [medListOpen, setMedListOpen] = useState(false)

  const { data, isLoading } = useMonthlyCalendar(year, month)
  const { data: medications } = useMedications()

  const medMap = useMemo(() => {
    const map: Record<string, MedicationItem> = {}
    medications?.forEach((m) => { map[m.id] = m })
    return map
  }, [medications])

  const eventsByDate = useMemo(() => {
    const map: Record<string, CalendarEvent[]> = {}
    data?.items.forEach((ev) => {
      if (!map[ev.event_date]) map[ev.event_date] = []
      map[ev.event_date].push(ev)
    })
    return map
  }, [data])

  const selectedEvents = eventsByDate[selectedDate] ?? []

  const selectedEventsByTime = useMemo(() => {
    const map: Record<string, CalendarEvent[]> = {}
    selectedEvents.forEach((ev) => {
      if (!map[ev.scheduled_time]) map[ev.scheduled_time] = []
      map[ev.scheduled_time].push(ev)
    })
    const toMinutes = (t: string) => { const [h, m] = t.split(':').map(Number); return h * 60 + (m || 0) }
    return Object.entries(map).sort(([a], [b]) => toMinutes(a) - toMinutes(b))
  }, [selectedEvents])

  const firstDay = new Date(year, month - 1, 1).getDay()
  const daysInMonth = new Date(year, month, 0).getDate()

  function prevMonth() {
    if (month === 1) { setYear((y) => y - 1); setMonth(12) }
    else setMonth((m) => m - 1)
  }
  function nextMonth() {
    if (month === 12) { setYear((y) => y + 1); setMonth(1) }
    else setMonth((m) => m + 1)
  }

  function toDateStr(day: number) {
    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col gap-4 pb-6 max-w-4xl mx-auto w-full">
      <PageHeader
        title="캘린더"
        description="복약 일정을 확인하고 의약품을 관리하세요."
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMedListOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <ListIcon />
              의약품 목록
            </button>
            <button
              onClick={() => setAddMedOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-white"
              style={{ background: '#1D9E75' }}
            >
              <PlusIcon />
              의약품 등록
            </button>
          </div>
        }
      />

      {/* ── 월 캘린더 ── */}
      <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500">
            <ChevronLeftIcon />
          </button>
          <p className="text-base font-bold text-gray-800">{year}년 {month}월</p>
          <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500">
            <ChevronRightIcon />
          </button>
        </div>

        <div className="flex items-center justify-end gap-3 mb-3">
          {(['TAKEN', 'MISSED', 'PENDING'] as const).map((s) => (
            <div key={s} className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full shrink-0 ${STATUS_CONFIG[s].dot}`} />
              <span className="text-[11px] text-gray-400">{STATUS_CONFIG[s].label}</span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 mb-1 border-b border-gray-100 pb-1">
          {WEEKDAYS.map((d, i) => (
            <p key={d} className={`text-center text-sm font-bold py-1 ${
              i === 0 ? 'text-red-400' : i === 6 ? 'text-blue-400' : 'text-gray-400'
            }`}>{d}</p>
          ))}
        </div>

        {isLoading ? (
          <Skeleton className="h-44 w-full rounded-xl" />
        ) : (
          <div className="grid grid-cols-7">
            {Array.from({ length: firstDay }).map((_, i) => <div key={`pad-${i}`} />)}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1
              const ds = toDateStr(day)
              const events = eventsByDate[ds] ?? []
              const isSelected = ds === selectedDate
              const isToday = ds === todayStr
              const dow = (firstDay + i) % 7

              return (
                <button
                  key={day}
                  onClick={() => setSelectedDate(ds)}
                  className="flex flex-col items-center py-1.5 rounded-xl hover:bg-gray-50 transition-colors"
                >
                  <span className={`text-sm font-medium w-7 h-7 flex items-center justify-center rounded-full ${
                    isToday
                      ? 'bg-[#1D9E75] text-white'
                      : isSelected
                      ? 'border border-[#1D9E75] text-[#1D9E75]'
                      : dow === 0
                      ? 'text-red-400'
                      : dow === 6
                      ? 'text-blue-400'
                      : 'text-gray-700'
                  }`}>
                    {day}
                  </span>
                  <div className="flex gap-0.5 mt-0.5 h-1.5 items-center">
                    {events.slice(0, 3).map((ev, idx) => (
                      <span
                        key={idx}
                        className={`w-1.5 h-1.5 rounded-full ${STATUS_CONFIG[ev.status as keyof typeof STATUS_CONFIG]?.dot ?? 'bg-gray-300'}`}
                      />
                    ))}
                    {events.length > 3 && (
                      <span className="text-[8px] font-bold text-gray-400 leading-none">+{events.length - 3}</span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* ── 선택한 날 일정 ── */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between px-1">
          <p className="text-sm font-semibold text-gray-700">
            {selectedDate.replace(/-/g, '. ')}
          </p>
          <div className="flex items-center gap-2">
            <p className="text-xs text-gray-400">{selectedEvents.length}건</p>
            <button
              onClick={() => setAddEventOpen(true)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border border-[#1D9E75] text-[#1D9E75] hover:bg-emerald-50 transition-colors"
            >
              <PlusIcon />
              일정 추가
            </button>
          </div>
        </div>

        {selectedEvents.length === 0 ? (
          <div className="rounded-2xl bg-white border border-gray-100 shadow-sm py-10 flex items-center justify-center">
            <p className="text-sm text-gray-400">이 날 예정된 복약 일정이 없습니다.</p>
          </div>
        ) : (
          selectedEventsByTime.map(([time, events]) => (
            <TimeSlotGroup key={time} time={time} events={events} medMap={medMap} />
          ))
        )}
      </div>

      {addMedOpen && <MedicationModal onClose={() => setAddMedOpen(false)} />}
      {medListOpen && <MedicationListSheet onClose={() => setMedListOpen(false)} />}
      {addEventOpen && <CalendarEventAddModal defaultDate={selectedDate} onClose={() => setAddEventOpen(false)} />}
    </div>
  )
}

// ─── 아이콘 ──────────────────────────────────────────────────────────────────

function PillIcon() {
  return (
    <svg className="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  )
}
function XIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
function PlusIcon() {
  return (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
    </svg>
  )
}
function EditIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
    </svg>
  )
}
function TrashIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  )
}
function ListIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  )
}
function ChevronLeftIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  )
}
function ChevronRightIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  )
}
