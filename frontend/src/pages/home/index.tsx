import { Link } from 'react-router-dom'
import { PageHeader } from '@/shared/ui/PageHeader'
import { toast } from '@/shared/lib/toast'
import { useCurrentUser } from '@/entities/user/api'
import { useMedicalRecords } from '@/entities/medical-record/api'
import { useGuides } from '@/entities/guide/api'
import { useNotifications } from '@/entities/notification/api'
import { useChatSessions } from '@/entities/chatbot/api'
import { Skeleton } from '@/components/ui/skeleton'

interface StatCardProps {
  icon: React.ReactNode
  label: string
  count: number | undefined
  isLoading: boolean
  href: string
}

function StatCard({ icon, label, count, isLoading, href }: StatCardProps) {
  return (
    <div className="rounded-2xl p-4 bg-white shadow-sm border border-gray-100 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <div
          className="shrink-0 flex h-8 w-8 items-center justify-center rounded-lg"
          style={{ background: '#E1F5EE', color: '#1D9E75' }}
        >
          {icon}
        </div>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
      {isLoading ? (
        <Skeleton className="h-7 w-14 rounded" />
      ) : (
        <p className="text-2xl font-bold text-gray-800">
          <Link to={href} className="hover:underline underline-offset-2">{count ?? 0}</Link>
          <span className="text-sm font-medium text-gray-400 ml-1">건</span>
        </p>
      )}
    </div>
  )
}

export function HomePage() {
  const { data: user, isLoading } = useCurrentUser()
  const { data: records, isLoading: recordsLoading } = useMedicalRecords()
  const { data: guides, isLoading: guidesLoading } = useGuides()
  const { data: notifications, isLoading: notificationsLoading } = useNotifications()
  const { data: sessions, isLoading: sessionsLoading } = useChatSessions()

  const greeting = (() => {
    const hour = new Date().getHours()
    if (hour < 12) return '좋은 아침이에요'
    if (hour < 18) return '좋은 오후예요'
    return '좋은 저녁이에요'
  })()

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title="홈"
        description="건강 기록을 기반으로 맞춤 가이드를 제공합니다."
      />

      <div className="pb-4 flex flex-col gap-6">
        {/* 웰컴 배너 */}
        <div
          className="rounded-2xl px-5 py-4"
          style={{ background: 'linear-gradient(135deg, #1D9E75 0%, #0F6E56 100%)' }}
        >
          {isLoading ? (
            <div className="h-5 w-40 rounded bg-white/20 animate-pulse" />
          ) : (
            <p className="text-white font-semibold text-base">
              {greeting}, {user?.name ?? '사용자'}님!
            </p>
          )}
          <p className="text-white/80 text-xs mt-1">
            오늘도 건강한 하루 되세요.
          </p>
          <button
            onClick={() =>
              toast.success('건강 팁', {
                description: '물을 하루 8잔 이상 마시면 체내 독소 배출에 도움이 됩니다.',
              })
            }
            className="mt-3 text-xs font-medium px-3 py-1.5 rounded-lg bg-white/20 text-white hover:bg-white/30 transition-colors"
          >
            오늘의 건강 팁 보기
          </button>
        </div>

        {/* 통계 카드 */}
        <section>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
            나의 현황
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard icon={<MedicalIcon />} label="의료기록" count={records?.length} isLoading={recordsLoading} href="/medical-record" />
            <StatCard icon={<BookIcon />} label="가이드" count={guides?.length} isLoading={guidesLoading} href="/guide" />
            <StatCard icon={<BellIcon />} label="활성 알림" count={notifications?.filter(n => n.is_active).length} isLoading={notificationsLoading} href="/notification" />
            <StatCard icon={<ChatIcon />} label="챗봇 세션" count={sessions?.length} isLoading={sessionsLoading} href="/chatbot" />
          </div>
        </section>

      </div>
    </div>
  )
}

function MedicalIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  )
}

function BookIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
  )
}

function ChatIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
    </svg>
  )
}

function BellIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  )
}
