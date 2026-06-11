import { useState, useMemo } from 'react'
import { PageHeader } from '@/shared/ui/PageHeader'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useMonthlyCalendar, useUpdateEventStatus, useDeleteCalendarEvent, useCreateCalendarEvent } from '@/entities/calendar/api'
import { useMedications } from '@/entities/medication/api'
import type { CalendarEvent } from '@/entities/calendar/model'
import type { MedicationItem } from '@/entities/medication/model'
import { getDrugCategory } from '@/shared/lib/drug-category'

const STATUS_CONFIG = {
  TAKEN:   { label: '복용 완료', active: 'bg-emerald-100 text-emerald-600', dot: 'bg-emerald-400' },
  MISSED:  { label: '미복용',   active: 'bg-red-100 text-red-500',         dot: 'bg-red-400' },
  PENDING: { label: '예정',     active: 'bg-gray-100 text-gray-500',       dot: 'bg-gray-300' },
}

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

function formatTime(time: string): string {
  const [hourStr, minuteStr] = time.split(':')
  const hour = parseInt(hourStr, 10)
  const ampm = hour < 12 ? '오전' : '오후'
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
  return `${ampm} ${String(displayHour).padStart(2, '0')}:${minuteStr}`
}

function EventCard({ item, medication }: { item: CalendarEvent; medication?: MedicationItem }) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { mutate: updateStatus, isPending: isUpdating } = useUpdateEventStatus()
  const { mutate: remove, isPending: isDeleting } = useDeleteCalendarEvent()

  const category = medication ? getDrugCategory(medication.drug_name) : null
  const displayName = category ?? medication?.drug_name ?? null

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-800">{formatTime(item.scheduled_time)}</p>
          {medication && (
            <div className="flex items-center gap-1.5 mt-1 flex-wrap">
              {category && (
                <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[#1D9E75]/10 text-[#1D9E75]">
                  {category}
                </span>
              )}
              <p className="text-xs font-medium text-gray-700">{medication.drug_name}</p>
            </div>
          )}
          {item.note && <p className="text-xs text-gray-500 mt-0.5 truncate">{item.note}</p>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5 gap-0.5">
            {(['TAKEN', 'MISSED', 'PENDING'] as const).map((s) => (
              <button
                key={s}
                onClick={() => updateStatus({ id: item.id, status: s })}
                disabled={isUpdating}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all disabled:opacity-60 ${
                  item.status === s
                    ? STATUS_CONFIG[s].active + ' shadow-sm'
                    : 'text-gray-400 hover:text-gray-600'
                }`}
              >
                {STATUS_CONFIG[s].label}
              </button>
            ))}
          </div>
          <button
            onClick={() => setDeleteOpen(true)}
            disabled={isDeleting}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-50 transition-colors disabled:opacity-40"
          >
            <TrashIcon />
          </button>
        </div>
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

const INPUT_CLS = 'rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10 w-full'

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
      { onSuccess: onClose },
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
          {/* 날짜 (읽기 전용) */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-500">날짜</label>
            <div className="rounded-xl border border-gray-100 bg-gray-50 px-3 py-2.5 text-sm text-gray-500">
              {defaultDate.replace(/-/g, '. ')}
            </div>
          </div>

          {/* 의약품 선택 */}
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

          {/* 복약 시간 */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-500">복약 시간</label>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className={INPUT_CLS} />
          </div>

          {/* 메모 */}
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

export function CalendarPage() {
  const today = new Date()
  const todayStr = today.toISOString().slice(0, 10)

  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [selectedDate, setSelectedDate] = useState(todayStr)
  const [addOpen, setAddOpen] = useState(false)

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
      <PageHeader title="캘린더" description="복약 일정을 확인하세요." />

      {/* ── 월 캘린더 ── */}
      <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-5">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-4">
          <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500">
            <ChevronLeftIcon />
          </button>
          <p className="text-base font-bold text-gray-800">{year}년 {month}월</p>
          <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500">
            <ChevronRightIcon />
          </button>
        </div>

        {/* 범례 */}
        <div className="flex items-center justify-end gap-3 mb-3">
          {(['TAKEN', 'MISSED', 'PENDING'] as const).map((s) => (
            <div key={s} className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full shrink-0 ${STATUS_CONFIG[s].dot}`} />
              <span className="text-[11px] text-gray-400">{STATUS_CONFIG[s].label}</span>
            </div>
          ))}
        </div>

        {/* 요일 헤더 */}
        <div className="grid grid-cols-7 mb-1 border-b border-gray-100 pb-1">
          {WEEKDAYS.map((d, i) => (
            <p key={d} className={`text-center text-sm font-bold py-1 ${
              i === 0 ? 'text-red-400' : i === 6 ? 'text-blue-400' : 'text-gray-400'
            }`}>{d}</p>
          ))}
        </div>

        {/* 날짜 그리드 */}
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
              onClick={() => setAddOpen(true)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-white"
              style={{ background: '#1D9E75' }}
            >
              <PlusIcon />
              추가
            </button>
          </div>
        </div>

        {selectedEvents.length === 0 ? (
          <div className="rounded-2xl bg-white border border-gray-100 shadow-sm py-10 flex items-center justify-center">
            <p className="text-sm text-gray-400">이 날 예정된 복약 일정이 없습니다.</p>
          </div>
        ) : (
          selectedEvents.map((ev) => <EventCard key={ev.id} item={ev} medication={medMap[ev.medication_id]} />)
        )}
      </div>

      {addOpen && <CalendarEventAddModal defaultDate={selectedDate} onClose={() => setAddOpen(false)} />}
    </div>
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
function TrashIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  )
}
