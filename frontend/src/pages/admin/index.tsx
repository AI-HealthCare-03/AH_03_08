import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/app/providers/auth-store'
import { apiClient } from '@/shared/api/client'

interface FeedbackItem {
  feedback_id: string
  user_id: number
  guide_id: string
  rating: number
  comment: string | null
  status: string
  created_at: string
}

interface MetricsSummary {
  ocr: { total: number; failed: number; success_rate_pct: number }
  llm: { total: number; failed: number; success_rate_pct: number }
  p95_latency_ms: number | null
  daily_guides: { date: string; guide_count: number }[]
}

interface UserItem {
  user_id: number
  email: string
  name: string
  is_admin: boolean
  is_active: boolean
  created_at: string
}

export function AdminPage() {
  const navigate = useNavigate()
  const isAdmin = useAuthStore((s) => s.isAdmin)
  const [tab, setTab] = useState<'metrics' | 'feedbacks' | 'users'>('metrics')
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null)
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([])
  const [users, setUsers] = useState<UserItem[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isAdmin) {
      navigate('/home', { replace: true })
    }
  }, [isAdmin])

  useEffect(() => {
    setLoading(true)
    if (tab === 'metrics') {
      apiClient.get('/admin/metrics/summary')
        .then(r => setMetrics(r.data.data))
        .finally(() => setLoading(false))
    } else if (tab === 'feedbacks') {
      apiClient.get('/admin/feedbacks')
        .then(r => setFeedbacks(r.data.data.items))
        .finally(() => setLoading(false))
    } else if (tab === 'users') {
      apiClient.get('/admin/users')
        .then(r => setUsers(r.data.data.items))
        .finally(() => setLoading(false))
    }
  }, [tab])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold" style={{ color: '#1D9E75' }}>MediLog 관리자</h1>
        <button
          onClick={() => { useAuthStore.getState().logout(); navigate('/auth/login') }}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          로그아웃
        </button>
      </div>

      {/* 탭 */}
      <div className="bg-white border-b px-6 flex gap-6">
        {(['metrics', 'feedbacks', 'users'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? 'border-[#1D9E75] text-[#1D9E75]' : 'border-transparent text-gray-500'
            }`}
          >
            {t === 'metrics' ? 'AI 지표' : t === 'feedbacks' ? '피드백' : '사용자'}
          </button>
        ))}
      </div>

      <div className="p-6">
        {loading && <p className="text-sm text-gray-400">로딩 중...</p>}

        {/* AI 지표 */}
        {tab === 'metrics' && metrics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">OCR 성공률</p>
              <p className="text-2xl font-bold text-gray-800">{metrics.ocr.success_rate_pct}%</p>
              <p className="text-xs text-gray-400 mt-1">총 {metrics.ocr.total}건 / 실패 {metrics.ocr.failed}건</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">LLM 가이드 성공률</p>
              <p className="text-2xl font-bold text-gray-800">{metrics.llm.success_rate_pct}%</p>
              <p className="text-xs text-gray-400 mt-1">총 {metrics.llm.total}건 / 실패 {metrics.llm.failed}건</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">P95 지연시간</p>
              <p className="text-2xl font-bold text-gray-800">
                {metrics.p95_latency_ms != null ? `${metrics.p95_latency_ms}ms` : '-'}
              </p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm md:col-span-3">
              <p className="text-xs text-gray-500 mb-3">최근 7일 가이드 생성</p>
              <div className="flex items-end gap-2 h-24">
                {metrics.daily_guides.map(d => (
                  <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className="w-full rounded-t"
                      style={{
                        background: '#1D9E75',
                        height: `${Math.max(4, (d.guide_count / Math.max(...metrics.daily_guides.map(x => x.guide_count), 1)) * 80)}px`
                      }}
                    />
                    <p className="text-xs text-gray-400">{d.date.slice(5)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 피드백 */}
        {tab === 'feedbacks' && (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs">
                <tr>
                  <th className="px-4 py-3 text-left">사용자</th>
                  <th className="px-4 py-3 text-left">평점</th>
                  <th className="px-4 py-3 text-left">코멘트</th>
                  <th className="px-4 py-3 text-left">상태</th>
                  <th className="px-4 py-3 text-left">날짜</th>
                </tr>
              </thead>
              <tbody>
                {feedbacks.map(f => (
                  <tr key={f.feedback_id} className="border-t border-gray-100">
                    <td className="px-4 py-3">{f.user_id}</td>
                    <td className="px-4 py-3">{'★'.repeat(f.rating)}{'☆'.repeat(5 - f.rating)}</td>
                    <td className="px-4 py-3 text-gray-500">{f.comment || '-'}</td>
                    <td className="px-4 py-3">{f.status}</td>
                    <td className="px-4 py-3 text-gray-400">{f.created_at?.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 사용자 */}
        {tab === 'users' && (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs">
                <tr>
                  <th className="px-4 py-3 text-left">이름</th>
                  <th className="px-4 py-3 text-left">이메일</th>
                  <th className="px-4 py-3 text-left">관리자</th>
                  <th className="px-4 py-3 text-left">활성</th>
                  <th className="px-4 py-3 text-left">가입일</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.user_id} className="border-t border-gray-100">
                    <td className="px-4 py-3 font-medium">{u.name}</td>
                    <td className="px-4 py-3 text-gray-500">{u.email}</td>
                    <td className="px-4 py-3">{u.is_admin ? '✅' : '-'}</td>
                    <td className="px-4 py-3">{u.is_active ? '✅' : '❌'}</td>
                    <td className="px-4 py-3 text-gray-400">{u.created_at?.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}