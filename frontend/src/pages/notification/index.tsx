import { useState, useMemo } from 'react'
import { PageHeader } from '@/shared/ui/PageHeader'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useNotifications, useCreateNotification, useUpdateNotification, useDeleteNotification } from '@/entities/notification/api'
import { useMedications, useAddMedication, useUpdateMedication, useDeleteMedication } from '@/entities/medication/api'
import type { MedicationItem } from '@/entities/medication/model'
import type { NotificationItem } from '@/entities/notification/model'
import { getDrugCategory, formatFrequency } from '@/shared/lib/drug-category'

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

function NotificationRow({ item }: { item: NotificationItem }) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { mutate: update, isPending: isToggling } = useUpdateNotification()
  const { mutate: remove, isPending: isDeleting } = useDeleteNotification()
  const label = timeSlotLabel(item.scheduled_time)

  return (
    <div className={`flex items-center gap-3 px-4 py-3 border-t border-gray-50 transition-opacity ${item.is_active ? '' : 'opacity-40'}`}>
      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md shrink-0 ${SLOT_STYLE[label]}`}>
        {label}
      </span>
      <span className="flex-1 text-sm font-medium text-gray-800">{formatTime(item.scheduled_time)}</span>
      <div className="flex items-center gap-2 shrink-0">
        <Toggle checked={item.is_active} disabled={isToggling} onChange={() => update({ id: item.id, is_active: !item.is_active })} />
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
        description="삭제된 알림은 복구할 수 없습니다."
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

function MedicationGroup({ medication, notifications }: { medication: MedicationItem; notifications: NotificationItem[] }) {
  const [alarmOpen, setAlarmOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { mutate: remove, isPending: isDeleting } = useDeleteMedication()
  const meta = [medication.dosage, formatFrequency(medication.frequency), medication.instructions].filter(Boolean).join(' · ')
  const activeCount = notifications.filter((n) => n.is_active).length
  const sourceBadge = medication.record_type != null ? SOURCE_BADGE[medication.record_type] : null

  return (
    <>
      <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
        {/* 약물 헤더 */}
        <div className="flex items-center gap-3 px-4 py-4">
          <div className="h-9 w-9 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
            <PillIcon />
          </div>
          <div className="flex-1 min-w-0">
            {(() => {
              const category = getDrugCategory(medication.drug_name)
              return (
                <div className="flex items-center gap-1.5 flex-wrap">
                  {category && (
                    <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[#1D9E75]/10 text-[#1D9E75] shrink-0">
                      {category}
                    </span>
                  )}
                  <p className="text-xs font-medium text-gray-700 truncate">{medication.drug_name}</p>
                </div>
              )
            })()}
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
              {(sourceBadge || medication.source_name) && meta && (
                <span className="text-gray-300 text-xs">·</span>
              )}
              <span className="text-xs text-gray-400 truncate">{meta || (!sourceBadge && !medication.source_name ? '복용 정보 없음' : '')}</span>
              {notifications.length > 0 && (
                <span className="text-[#1D9E75] text-xs font-medium shrink-0">알림 {activeCount}/{notifications.length}</span>
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

        {/* 알림 없을 때 안내 */}
        {notifications.length === 0 && (
          <div className="border-t border-gray-50 px-4 py-3 flex items-center gap-2">
            <span className="text-xs text-gray-300">설정된 알림이 없습니다</span>
          </div>
        )}

        {/* 알림 시간 목록 */}
        {notifications.map((n) => (
          <NotificationRow key={n.id} item={n} />
        ))}

        {/* 알림 추가 버튼 */}
        <button
          onClick={() => setAlarmOpen(true)}
          className="w-full flex items-center justify-center gap-1.5 py-3 border-t border-dashed border-gray-200 text-xs font-semibold text-gray-400 hover:text-[#1D9E75] hover:bg-emerald-50/40 transition-colors"
        >
          <PlusSmallIcon />
          알림 시간 추가
        </button>
      </div>

      {alarmOpen && (
        <NotificationAddModal medicationId={medication.id} drugName={medication.drug_name} onClose={() => setAlarmOpen(false)} />
      )}
      {editOpen && <MedicationModal editItem={medication} onClose={() => setEditOpen(false)} />}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={`'${medication.drug_name}'을 삭제하시겠습니까?`}
        description="의약품을 삭제하면 연결된 알림도 함께 삭제됩니다."
        confirmLabel="삭제"
        variant="danger"
        onConfirm={() => remove(medication.id)}
      />
    </>
  )
}

// ─── 상수 & 유틸 ─────────────────────────────────────────────────────────────

const DOSAGE_UNITS      = ['mg', 'g', 'ml', 'mcg', 'IU', '정', '캡슐', '포']
const FREQUENCY_OPTIONS = ['하루 1회', '하루 2회', '하루 3회', '하루 4회', '필요시 복용']
const INSTRUCTION_OPTIONS = ['식전 30분', '식후 30분', '식후 즉시', '취침 전', '공복']

const INPUT_CLS = 'rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-[#1D9E75] focus:ring-2 focus:ring-[#1D9E75]/10 w-full'

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

function parseDosage(dosage: string | null): { num: string; unit: string } {
  if (!dosage) return { num: '', unit: 'mg' }
  const match = dosage.match(/^([\d.]+)(.+)$/)
  if (match) return { num: match[1], unit: DOSAGE_UNITS.includes(match[2]) ? match[2] : 'mg' }
  return { num: '', unit: 'mg' }
}

// ─── 의약품 등록 / 수정 모달 ──────────────────────────────────────────────────

function MedicationModal({ onClose, editItem }: { onClose: () => void; editItem?: MedicationItem }) {
  const parsed = parseDosage(editItem?.dosage ?? null)
  const [drugName, setDrugName] = useState(editItem?.drug_name ?? '')
  const [dosageNum, setDosageNum] = useState(parsed.num)
  const [dosageUnit, setDosageUnit] = useState(parsed.unit)
  const [frequency, setFrequency] = useState(editItem?.frequency ?? '')
  const [instructions, setInstructions] = useState(editItem?.instructions ?? '')
  const { mutate: add, isPending: isAdding } = useAddMedication()
  const { mutate: update, isPending: isUpdating } = useUpdateMedication()
  const isPending = isAdding || isUpdating

  function handleSubmit() {
    if (!drugName.trim()) return
    const dosage = dosageNum.trim() ? `${dosageNum.trim()}${dosageUnit}` : undefined
    const body = { drug_name: drugName.trim(), dosage, frequency: frequency || undefined, instructions: instructions || undefined }
    if (editItem) update({ id: editItem.id, ...body }, { onSuccess: onClose })
    else add(body, { onSuccess: onClose })
  }

  return (
    <BottomSheet onClose={onClose} title={editItem ? '의약품 수정' : '의약품 등록'}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">약품명 <span className="text-red-400">*</span></label>
          <input type="text" value={drugName} onChange={(e) => setDrugName(e.target.value)}
            placeholder="예: 타이레놀" autoFocus className={INPUT_CLS} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">용량</label>
          <input type="number" step="any" value={dosageNum} onChange={(e) => setDosageNum(e.target.value)}
            placeholder="예: 500" className={INPUT_CLS} />
          <OptionGroup options={DOSAGE_UNITS} value={dosageUnit} onChange={setDosageUnit} allowDeselect={false} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">복용 횟수</label>
          <OptionGroup options={FREQUENCY_OPTIONS} value={frequency} onChange={setFrequency} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">복용 시기</label>
          <OptionGroup options={INSTRUCTION_OPTIONS} value={instructions} onChange={setInstructions} />
        </div>
      </div>
      <div className="flex gap-2 pt-2">
        <button onClick={onClose} className="flex-1 py-3 rounded-xl text-sm text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors">
          취소
        </button>
        <button onClick={handleSubmit} disabled={!drugName.trim() || isPending}
          className="flex-1 py-3 rounded-xl text-sm text-white font-semibold disabled:opacity-50 transition-colors"
          style={{ background: '#1D9E75' }}>
          {isPending ? '저장 중...' : editItem ? '저장' : '등록'}
        </button>
      </div>
    </BottomSheet>
  )
}

// ─── 알림 추가 모달 ────────────────────────────────────────────────────────────

function NotificationAddModal({ medicationId, drugName, onClose }: { medicationId: string; drugName: string; onClose: () => void }) {
  const [title, setTitle] = useState(`${drugName} 복약 알림`)
  const [time, setTime] = useState('08:00')
  const { mutate: create, isPending } = useCreateNotification()

  function handleSubmit() {
    if (!title.trim() || !time) return
    create({ medication_id: medicationId, title: title.trim(), type: 'push', scheduled_time: `${time}:00` }, { onSuccess: onClose })
  }

  const label = timeSlotLabel(`${time}:00`)

  return (
    <BottomSheet onClose={onClose} title="알림 시간 추가">
      <div className="flex flex-col gap-4">
        {/* 미리보기 */}
        <div className="rounded-xl bg-gray-50 border border-gray-100 px-4 py-3 flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-[#1D9E75] flex items-center justify-center shrink-0">
            <BellSolidIcon />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-gray-700 truncate">{title || '알림 제목'}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              <span className={`inline-block text-[10px] font-semibold px-1.5 py-0.5 rounded mr-1.5 ${SLOT_STYLE[label]}`}>{label}</span>
              {time ? formatTime(`${time}:00`) : '시간 선택'}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">
            알림 제목
            <span className="ml-1.5 font-normal text-gray-400">· 알림 수신 시 표시되는 텍스트</span>
          </label>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className={INPUT_CLS} />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-gray-500">복약 시간</label>
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className={INPUT_CLS} />
        </div>
      </div>

      <div className="flex gap-2 pt-2">
        <button onClick={onClose} className="flex-1 py-3 rounded-xl text-sm text-gray-500 border border-gray-200 hover:bg-gray-50 transition-colors">
          취소
        </button>
        <button onClick={handleSubmit} disabled={!title.trim() || !time || isPending}
          className="flex-1 py-3 rounded-xl text-sm text-white font-semibold disabled:opacity-50 transition-colors"
          style={{ background: '#1D9E75' }}>
          {isPending ? '저장 중...' : '추가'}
        </button>
      </div>
    </BottomSheet>
  )
}

// ─── 공통 바텀시트 래퍼 ────────────────────────────────────────────────────────

function BottomSheet({ onClose, title, children }: { onClose: () => void; title: string; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full sm:max-w-md bg-white rounded-t-3xl sm:rounded-2xl shadow-xl px-6 pt-6 pb-8 flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <p className="text-base font-bold text-gray-900">{title}</p>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors">
            <XIcon />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

// ─── 페이지 ────────────────────────────────────────────────────────────────────

export function NotificationPage() {
  const { data: medications, isLoading: medLoading } = useMedications()
  const { data: notifications, isLoading: notiLoading } = useNotifications()
  const [medicationModalOpen, setMedicationModalOpen] = useState(false)

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
        description="복약 시간에 맞춰 알림을 받아보세요."
        action={
          <button
            onClick={() => setMedicationModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-white"
            style={{ background: '#1D9E75' }}
          >
            <PlusSmallIcon />
            의약품 등록
          </button>
        }
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
            <p className="text-xs text-gray-400 mt-1">의약품을 등록하고 복약 알림을 설정해보세요.</p>
          </div>
          <button
            onClick={() => setMedicationModalOpen(true)}
            className="mt-1 px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
            style={{ background: '#1D9E75' }}
          >
            의약품 등록하기
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

      {medicationModalOpen && <MedicationModal onClose={() => setMedicationModalOpen(false)} />}
    </div>
  )
}

// ─── 아이콘 ────────────────────────────────────────────────────────────────────

function XIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
function XSmallIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
function PlusSmallIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
function BellSolidIcon() {
  return (
    <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 24 24">
      <path d="M5.85 3.5a.75.75 0 00-1.117-1 9.719 9.719 0 00-2.348 4.876.75.75 0 001.479.248A8.219 8.219 0 015.85 3.5zM19.267 2.5a.75.75 0 10-1.118 1 8.22 8.22 0 011.987 4.124.75.75 0 001.48-.248A9.72 9.72 0 0019.266 2.5z" />
      <path fillRule="evenodd" d="M12 2.25A6.75 6.75 0 005.25 9v.75a8.217 8.217 0 01-2.119 5.52.75.75 0 00.298 1.206c1.544.57 3.16.99 4.831 1.243a3.75 3.75 0 107.48 0 24.583 24.583 0 004.83-1.244.75.75 0 00.298-1.205 8.217 8.217 0 01-2.118-5.52V9A6.75 6.75 0 0012 2.25zM9.75 18c0-.034 0-.067.002-.1a25.05 25.05 0 004.496 0l.002.1a2.25 2.25 0 11-4.5 0z" clipRule="evenodd" />
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
