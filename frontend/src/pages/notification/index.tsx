import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { PageHeader } from '@/shared/ui/PageHeader'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useNotifications, useUpdateNotification, useDeleteNotification } from '@/entities/notification/api'
import { useMedications, useDrugClassFallback } from '@/entities/medication/api'
import type { MedicationItem } from '@/entities/medication/model'
import type { NotificationItem } from '@/entities/notification/model'
import { formatFrequency } from '@/shared/lib/drug-category'

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

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: () => void; disabled?: boolean }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none disabled:cursor-not-allowed ${
        checked ? 'bg-[#1D9E75]' : 'bg-gray-200'
      }`}
    >
      <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition duration-200 ${checked ? 'translate-x-5' : 'translate-x-0'}`} />
    </button>
  )
}

function periodText(startDate?: string | null, endDate?: string | null): string | null {
  const fmt = (d: string) => d.replace(/-/g, '.')
  if (startDate && endDate) {
    const days = Math.round((new Date(endDate).getTime() - new Date(startDate).getTime()) / 86400000) + 1
    return `${fmt(startDate)} ~ ${fmt(endDate)} · ${days}일간`
  }
  if (startDate) return `${fmt(startDate)} ~ 종료일 미정`
  if (endDate) return `~ ${fmt(endDate)}`
  return null
}

function NotificationRow({ item, startDate, endDate }: {
  item: NotificationItem
  startDate?: string | null
  endDate?: string | null
}) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { mutate: update, isPending: isToggling } = useUpdateNotification()
  const { mutate: remove, isPending: isDeleting } = useDeleteNotification()
  const label = timeSlotLabel(item.scheduled_time)
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`
  const isExpired = !!endDate && endDate < todayStr
  const period = periodText(startDate, endDate)

  return (
    <div className={`flex items-center gap-3 px-4 py-3 border-t border-gray-50 transition-opacity ${item.is_active ? '' : 'opacity-50'}`}>
      {isExpired ? (
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md shrink-0 bg-gray-100 text-gray-400">
          종료
        </span>
      ) : (
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md shrink-0 ${SLOT_STYLE[label]}`}>
          {label}
        </span>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-700">{formatTime(item.scheduled_time)}</p>
        {period && (
          <p className="text-[11px] text-gray-400 mt-0.5 truncate">{period}</p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Toggle checked={item.is_active} disabled={isToggling || isExpired} onChange={() => update({ id: item.id, is_active: !item.is_active })} />
        <button
          onClick={() => setDeleteOpen(true)}
          disabled={isDeleting}
          className="w-6 h-6 flex items-center justify-center rounded-md text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors disabled:opacity-40"
        >
          <XSmallIcon />
        </button>
      </div>
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="알림을 삭제하시겠습니까?"
        description="삭제된 알림과 연결된 미래 복약 일정도 함께 삭제됩니다."
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => remove(item.id)}
      />
    </div>
  )
}

const SOURCE_BADGE: Record<number, { label: string; bg: string; color: string }> = {
  0: { label: '처방전', bg: '#EFF6FF', color: '#1D4ED8' },
  1: { label: '약봉투', bg: '#FFF7ED', color: '#C2410C' },
}

function MedicationGroup({ medication, notifications }: {
  medication: MedicationItem
  notifications: NotificationItem[]
}) {
  const activeCount = notifications.filter((n) => n.is_active).length
  const sourceBadge = medication.record_type != null ? SOURCE_BADGE[medication.record_type] : null
  const category = useDrugClassFallback(medication.drug_name, medication.drug_class, medication.id)
  const displayCategory = category
  const meta = [medication.dosage, formatFrequency(medication.frequency), medication.instructions].filter(Boolean).join(' · ')
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`
  const isExpired = !!medication.end_date && medication.end_date < todayStr

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-4">
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
            <p className="text-xs font-medium text-gray-700 truncate">{medication.drug_name}</p>
            {isExpired && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-400 shrink-0">
                복용 종료
              </span>
            )}
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
            {meta && (
              <>
                {(sourceBadge || medication.source_name) && <span className="text-gray-300 text-xs">·</span>}
                <span className="text-xs text-gray-400 truncate">{meta}</span>
              </>
            )}
            {notifications.length > 0 && (
              <span className="text-[#1D9E75] text-xs font-medium shrink-0 ml-auto">
                알림 {activeCount}/{notifications.length}
              </span>
            )}
          </div>
        </div>
      </div>

      {notifications.length === 0 ? (
        <div className="border-t border-gray-50 px-4 py-3">
          <span className="text-xs text-gray-300">설정된 알림이 없습니다</span>
        </div>
      ) : (
        notifications.map((n) => (
          <NotificationRow key={n.id} item={n} startDate={medication.start_date} endDate={medication.end_date} />
        ))
      )}
    </div>
  )
}

export function NotificationPage() {
  const navigate = useNavigate()
  const { data: medications, isLoading: medLoading } = useMedications()
  const { data: notifications, isLoading: notiLoading } = useNotifications()

  const notificationsByMedication = useMemo(() => {
    const map: Record<string, NotificationItem[]> = {}
    notifications?.forEach((n) => {
      if (!map[n.medication_id]) map[n.medication_id] = []
      map[n.medication_id].push(n)
    })
    const toMinutes = (t: string) => { const [h, m] = t.split(':').map(Number); return h * 60 + m }
    Object.values(map).forEach((list) => list.sort((a, b) => toMinutes(a.scheduled_time) - toMinutes(b.scheduled_time)))
    return map
  }, [notifications])

  const isLoading = medLoading || notiLoading

  return (
    <div className="flex flex-col min-h-full gap-4 pb-6 max-w-3xl mx-auto w-full">
      <PageHeader
        title="알림 설정"
        description="복약 알림을 켜거나 끄세요."
      />

      {isLoading ? (
        <div className="flex flex-col gap-3">
          {[1, 2].map((i) => (
            <div key={i} className="rounded-2xl bg-white border border-gray-100 shadow-sm p-4 flex flex-col gap-3">
              <div className="flex gap-3">
                <Skeleton className="h-9 w-9 rounded-xl" />
                <div className="flex flex-col gap-2 flex-1">
                  <Skeleton className="h-4 w-32 rounded" />
                  <Skeleton className="h-3 w-48 rounded" />
                </div>
              </div>
              <Skeleton className="h-10 w-full rounded-xl" />
            </div>
          ))}
        </div>
      ) : !medications?.length ? (
        <div className="rounded-2xl bg-white border border-gray-100 shadow-sm py-16 flex flex-col items-center gap-3">
          <div className="h-14 w-14 rounded-2xl bg-gray-50 flex items-center justify-center">
            <PillIconLg />
          </div>
          <div className="text-center">
            <p className="text-sm font-semibold text-gray-700">등록된 의약품이 없습니다</p>
            <p className="text-xs text-gray-400 mt-1">캘린더에서 의약품을 등록하면 알림이 자동으로 설정됩니다.</p>
          </div>
          <button
            onClick={() => navigate('/calendar')}
            className="mt-1 px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
            style={{ background: '#1D9E75' }}
          >
            캘린더로 이동
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {medications.map((med) => (
            <MedicationGroup
              key={med.id}
              medication={med}
              notifications={notificationsByMedication[med.id] ?? []}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ─── 아이콘 ────────────────────────────────────────────────────────────────────

function XSmallIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
function PillIcon() {
  return (
    <svg className="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  )
}
function PillIconLg() {
  return (
    <svg className="h-7 w-7 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  )
}
