import { useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { StatusBadge } from '@/shared/ui/StatusBadge'
import { useCurrentUser } from '@/entities/user/api'
import { useMedicalRecords } from '@/entities/medical-record/api'
import { useGuides } from '@/entities/guide/api'
import { useNotifications } from '@/entities/notification/api'
import { useChatSessions } from '@/entities/chatbot/api'
import { useDailyCalendar, useUpdateEventStatus } from '@/entities/calendar/api'
import { useMedications } from '@/entities/medication/api'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'
import { getDrugCategory } from '@/shared/lib/drug-category'
import type { MedicationItem } from '@/entities/medication/model'

const PILL_COLORS = [
  { bg: 'bg-emerald-100', text: 'text-emerald-500' },
  { bg: 'bg-sky-100',     text: 'text-sky-500'     },
  { bg: 'bg-amber-100',   text: 'text-amber-500'   },
  { bg: 'bg-violet-100',  text: 'text-violet-500'  },
  { bg: 'bg-rose-100',    text: 'text-rose-500'    },
]

function formatTime(time: string): string {
  const [h, m] = time.split(':')
  const hour = parseInt(h, 10)
  const ampm = hour < 12 ? '오전' : '오후'
  const display = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
  return `${ampm} ${String(display).padStart(2, '0')}:${m}`
}

function StatCard({ label, count, isLoading, href }: { label: string; count: number | undefined; isLoading: boolean; href: string }) {
  return (
    <Link to={href} className="rounded-2xl bg-white border border-gray-100 shadow-sm p-3.5 flex flex-col gap-1 hover:bg-gray-50 transition-colors">
      <p className="text-xs text-gray-500">{label}</p>
      {isLoading
        ? <Skeleton className="h-6 w-10 rounded" />
        : <p className="text-xl font-bold text-gray-800">{count ?? 0}<span className="text-xs font-medium text-gray-400 ml-0.5">건</span></p>
      }
    </Link>
  )
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none ${checked ? 'bg-[#1D9E75]' : 'bg-gray-200'}`}
    >
      <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition duration-200 ${checked ? 'translate-x-5' : 'translate-x-0'}`} />
    </button>
  )
}

export function HomePage() {
  const navigate = useNavigate()
  const todayStr = new Date().toISOString().slice(0, 10)

  const { data: user, isLoading: userLoading } = useCurrentUser()
  const { data: records, isLoading: recordsLoading } = useMedicalRecords()
  const { data: guides, isLoading: guidesLoading } = useGuides()
  const { data: notifications, isLoading: notificationsLoading } = useNotifications()
  const { data: sessions, isLoading: sessionsLoading } = useChatSessions()
  const { data: todayEvents } = useDailyCalendar(todayStr)
  const { data: medications } = useMedications()
  const { mutate: updateStatus } = useUpdateEventStatus()

  const medMap = useMemo(() => {
    const map: Record<string, MedicationItem> = {}
    medications?.forEach(m => { map[m.id] = m })
    return map
  }, [medications])

  const activeNotifMedIds = useMemo(
    () => new Set(notifications?.filter(n => n.is_active).map(n => n.medication_id) ?? []),
    [notifications],
  )

  const todayActiveEvents = useMemo(() => {
    const toMin = (t: string) => { const [h, m] = t.split(':').map(Number); return h * 60 + m }
    return (todayEvents ?? [])
      .filter(e => activeNotifMedIds.has(e.medication_id))
      .sort((a, b) => toMin(a.scheduled_time) - toMin(b.scheduled_time))
  }, [todayEvents, activeNotifMedIds])

  const recentRecords = (records ?? []).slice(0, 2)
  const latestGuide = guides?.find(g => g.status === 'done') ?? guides?.[0]
  const activeNotifCount = notifications?.filter(n => n.is_active).length ?? 0

  return (
    <div className="flex flex-col gap-4 pb-6 max-w-3xl mx-auto w-full">

      {/* ── 헤더 ── */}
      <div className="flex items-start justify-between pt-1">
        <div>
          {userLoading
            ? <Skeleton className="h-7 w-44 rounded mb-1" />
            : <h1 className="text-xl font-bold text-gray-900">안녕하세요, {user?.name ?? '사용자'}님 👋</h1>
          }
          <p className="text-sm text-gray-500 mt-0.5">오늘도 건강 관리를 시작해봐요</p>
        </div>
        <button
          onClick={() => navigate('/medical-record')}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-semibold border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors shrink-0"
        >
          <UploadIcon />
          기록 업로드
        </button>
      </div>

      {/* ── 통계 ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <StatCard label="의료기록"   count={records?.length}      isLoading={recordsLoading}       href="/medical-record" />
        <StatCard label="가이드"     count={guides?.length}       isLoading={guidesLoading}         href="/guide" />
        <StatCard label="활성 알림"  count={activeNotifCount}     isLoading={notificationsLoading}  href="/notification" />
        <StatCard label="챗봇 세션"  count={sessions?.length ?? 0} isLoading={sessionsLoading}      href="/chatbot" />
      </div>

      {/* ── 최근 의료기록 + 최신 가이드 ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">

        {/* 최근 의료기록 */}
        <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-4">
          <p className="text-sm font-bold text-gray-800 mb-3">최근 의료기록</p>
          {recordsLoading ? (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-14 rounded-xl" />
              <Skeleton className="h-14 rounded-xl" />
            </div>
          ) : recentRecords.length === 0 ? (
            <p className="text-xs text-gray-400 py-5 text-center">업로드된 기록이 없습니다.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {recentRecords.map(record => {
                const meta = RECORD_TYPE_META[record.record_type]
                const institution = record.record_type === 'medicine_bag'
                  ? record.parsed_data?.pharmacy
                  : record.parsed_data?.hospital
                const date = record.parsed_data?.issued_at
                  ? new Date(record.parsed_data.issued_at).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
                  : new Date(record.created_at).toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' })

                return (
                  <div
                    key={record.id}
                    onClick={() => record.guide_id && navigate(`/guide?id=${record.guide_id}`)}
                    className={`flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl bg-gray-50 transition-colors ${record.guide_id ? 'cursor-pointer hover:bg-gray-100' : ''}`}
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-800 truncate">
                        {institution ? `${institution} ${meta?.label}` : meta?.label}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">{date}</p>
                    </div>
                    <StatusBadge status={record.status} />
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* 최신 가이드 */}
        <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-4 flex flex-col">
          <p className="text-sm font-bold text-gray-800 mb-3">최신 가이드</p>
          {guidesLoading ? (
            <div className="flex flex-col gap-2 flex-1">
              <Skeleton className="h-4 w-3/4 rounded" />
              <Skeleton className="h-3 w-full rounded" />
              <Skeleton className="h-3 w-4/5 rounded" />
            </div>
          ) : !latestGuide ? (
            <p className="text-xs text-gray-400 flex-1 py-2">생성된 가이드가 없습니다.</p>
          ) : (
            <div className="flex-1">
              {latestGuide.title && (
                <p className="text-xs font-semibold text-[#1D9E75] mb-1.5 truncate">{latestGuide.title}</p>
              )}
              <p className="text-xs text-gray-600 leading-relaxed line-clamp-4">
                {latestGuide.summary_text ?? '가이드 내용을 확인하세요.'}
              </p>
            </div>
          )}
          <Link
            to={latestGuide ? `/guide?id=${latestGuide.id}` : '/guide'}
            className="mt-3 text-xs font-semibold text-gray-400 hover:text-gray-700 transition-colors"
          >
            가이드 전체보기 →
          </Link>
        </div>
      </div>

      {/* ── 오늘 복약 알림 ── */}
      <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-4">
        <div className="flex items-center justify-between mb-0.5">
          <p className="text-sm font-bold text-gray-800">오늘 복약 알림</p>
          <Link to="/notification" className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors">
            <GearIcon />
            알림 관리
          </Link>
        </div>
        <p className="text-xs text-gray-400 mb-3">활성화된 알림만 표시</p>

        {todayActiveEvents.length === 0 ? (
          <div className="py-6 flex items-center justify-center">
            <p className="text-sm text-gray-400">오늘 예정된 복약 알림이 없습니다.</p>
          </div>
        ) : (
          <div className="flex flex-col divide-y divide-gray-50">
            {todayActiveEvents.map((event, idx) => {
              const med = medMap[event.medication_id]
              const rawName = med?.drug_name ?? '알 수 없음'
              const displayName = getDrugCategory(rawName) ?? rawName
              const dosage = med?.dosage ? ` ${med.dosage}` : ''
              const color = PILL_COLORS[idx % PILL_COLORS.length]
              const isTaken = event.status === 'TAKEN'

              return (
                <div key={event.id} className="flex items-center gap-3 py-3">
                  <div className={`h-9 w-9 rounded-xl flex items-center justify-center shrink-0 ${color.bg}`}>
                    <PillIcon className={`h-4 w-4 ${color.text}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{displayName}{dosage}</p>
                    <p className="text-xs text-gray-400">
                      {formatTime(event.scheduled_time)}
                      {med?.instructions ? ` · ${med.instructions}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      event.status === 'TAKEN'  ? 'bg-emerald-100 text-emerald-600' :
                      event.status === 'MISSED' ? 'bg-red-100 text-red-500' :
                                                  'bg-gray-100 text-gray-500'
                    }`}>
                      {event.status === 'TAKEN' ? '완료' : event.status === 'MISSED' ? '미복용' : '예정'}
                    </span>
                    <Toggle
                      checked={isTaken}
                      onChange={() => updateStatus({ id: event.id, status: isTaken ? 'PENDING' : 'TAKEN' })}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}
        <p className="text-xs text-gray-300 mt-2">토글을 켜면 복용 완료로 기록됩니다.</p>
      </div>

    </div>
  )
}

// ── 아이콘 ────────────────────────────────────────────────────────────────────

function UploadIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  )
}

function PillIcon({ className }: { className?: string }) {
  return (
    <svg className={className ?? 'h-4 w-4'} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  )
}

function GearIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 011.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.56.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.893.149c-.425.07-.765.383-.93.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 01-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.397.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 01-.12-1.45l.527-.737c.25-.35.273-.806.108-1.204-.165-.397-.505-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.765-.383.93-.78.165-.398.143-.854-.108-1.204l-.526-.738a1.125 1.125 0 01.12-1.45l.773-.773a1.125 1.125 0 011.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )
}
