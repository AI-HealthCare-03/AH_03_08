import { useState } from 'react'
import { PageHeader } from '@/shared/ui/PageHeader'
import { EmptyState } from '@/shared/ui/EmptyState'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'
import { PollingStatus } from '@/shared/ui/PollingStatus'
import { toast } from '@/shared/lib/toast'
import { useCurrentUser } from '@/entities/user/api'
import { Skeleton } from '@/components/ui/skeleton'

interface StatCardProps {
  icon: React.ReactNode
  label: string
  count: number | undefined
  isLoading: boolean
}

function StatCard({ icon, label, count, isLoading }: StatCardProps) {
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
        <p className="text-2xl font-bold text-gray-800">{count ?? 0}<span className="text-sm font-medium text-gray-400 ml-1">건</span></p>
      )}
    </div>
  )
}

export function HomePage() {
  const { data: user, isLoading } = useCurrentUser()
  const [confirmOpen, setConfirmOpen] = useState(false)

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

      <div className="px-4 md:px-6 pb-8 flex flex-col gap-6">
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
            <StatCard icon={<MedicalIcon />} label="의료기록" count={undefined} isLoading={isLoading} />
            <StatCard icon={<BookIcon />} label="가이드" count={undefined} isLoading={isLoading} />
            <StatCard icon={<BellIcon />} label="활성 알림" count={undefined} isLoading={isLoading} />
            <StatCard icon={<ChatIcon />} label="챗봇 세션" count={undefined} isLoading={isLoading} />
          </div>
        </section>

        {/* 공통 컴포넌트 데모 */}
        <section className="flex flex-col gap-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
            공통 컴포넌트 데모
          </p>

          {/* PollingStatus */}
          <div>
            <p className="text-xs text-gray-400 mb-2">PollingStatus</p>
            <PollingStatus message="AI가 의료기록을 분석 중입니다..." />
          </div>

          {/* EmptyState */}
          <div>
            <p className="text-xs text-gray-400 mb-2">EmptyState</p>
            <div className="rounded-2xl bg-white border border-gray-100 shadow-sm">
              <EmptyState
                icon={<MedicalIcon />}
                title="등록된 의료기록이 없습니다"
                description="처방전이나 검사 결과를 업로드하면 AI가 분석해 드립니다."
                action={{ label: '기록 추가하기', onClick: () => toast.info('의료기록 업로드로 이동') }}
              />
            </div>
          </div>

          {/* ConfirmDialog */}
          <div>
            <p className="text-xs text-gray-400 mb-2">ConfirmDialog</p>
            <button
              onClick={() => setConfirmOpen(true)}
              className="text-sm px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              삭제 확인 다이얼로그 열기
            </button>
            <ConfirmDialog
              open={confirmOpen}
              onOpenChange={setConfirmOpen}
              title="기록을 삭제하시겠습니까?"
              description="삭제된 기록은 복구할 수 없습니다."
              confirmLabel="삭제"
              variant="danger"
              onConfirm={() => toast.error('기록이 삭제되었습니다.')}
            />
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
