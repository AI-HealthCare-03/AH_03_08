import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/app/providers/auth-store'
import { apiClient } from '@/shared/api/client'

interface MetricsSummary {
  ocr: { total: number; failed: number; success_rate_pct: number }
  llm: { total: number; failed: number; success_rate_pct: number }
  p95_latency_ms: number | null
  daily_guides: { date: string; guide_count: number }[]
}

interface ModelComparison {
  version: string
  avg_latency_ms: number | null
  success_rate: number | null
  avg_rating: number | null
  total_count: number
}

interface ConsistencyItem {
  model_type: string
  mean_ms: number | null
  stddev_ms: number | null
  sample_count: number
}

interface FeedbackFlow {
  feedback_total: number
  positive_count: number
  negative_count: number
  improvement_trend: { date: string; model_type: string; avg_rating: number | null; success_rate: number | null }[]
}

interface TestReport {
  title: string
  generated_at: string
  summary: { total_feedback: number; positive_feedback: number; positive_rate_pct: number }
  model_comparison: { version: string; avg_rating: number | null }[]
  consistency_analysis: { model_type: string; mean_ms: number | null; stddev_ms: number | null; sample_count: number }[]
  async_processing: { description: string; queues: string[]; workers: string[]; beat_tasks: string[] }
  feedback_structure: { flow: string; implemented: boolean }
}

type Tab = 'metrics' | 'comparison' | 'consistency' | 'feedback-flow' | 'report' | 'feedbacks' | 'users'

export function AdminPage() {
  const navigate = useNavigate()
  const isAdmin = useAuthStore((s) => s.isAdmin)
  const [tab, setTab] = useState<Tab>('metrics')
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null)
  const [comparison, setComparison] = useState<ModelComparison[]>([])
  const [consistency, setConsistency] = useState<ConsistencyItem[]>([])
  const [feedbackFlow, setFeedbackFlow] = useState<FeedbackFlow | null>(null)
  const [report, setReport] = useState<TestReport | null>(null)
  const [feedbacks, setFeedbacks] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isAdmin) navigate('/home', { replace: true })
  }, [isAdmin])

  useEffect(() => {
    setLoading(true)
    const fetch = async () => {
      try {
        if (tab === 'metrics') {
          const r = await apiClient.get('/admin/metrics/summary')
          setMetrics(r.data.data)
        } else if (tab === 'comparison') {
          const r = await apiClient.get('/admin/metrics/model-comparison')
          setComparison(r.data.data)
        } else if (tab === 'consistency') {
          const r = await apiClient.get('/admin/metrics/consistency')
          setConsistency(r.data.data)
        } else if (tab === 'feedback-flow') {
          const r = await apiClient.get('/admin/metrics/feedback-flow')
          setFeedbackFlow(r.data.data)
        } else if (tab === 'report') {
          const r = await apiClient.get('/admin/report')
          setReport(r.data.data)
        } else if (tab === 'feedbacks') {
          const r = await apiClient.get('/admin/feedbacks')
          setFeedbacks(r.data.data.items)
        } else if (tab === 'users') {
          const r = await apiClient.get('/admin/users')
          setUsers(r.data.data.items)
        }
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [tab])

  const tabs: { key: Tab; label: string }[] = [
    { key: 'metrics', label: 'AI 지표' },
    { key: 'comparison', label: '모델 비교' },
    { key: 'consistency', label: '반복 테스트' },
    { key: 'feedback-flow', label: '피드백 흐름' },
    { key: 'report', label: '테스트 보고서' },
    { key: 'feedbacks', label: '피드백 목록' },
    { key: 'users', label: '사용자' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold" style={{ color: '#1D9E75' }}>MediLog 관리자</h1>
        <button
          onClick={() => { useAuthStore.getState().logout(); navigate('/auth/login') }}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          로그아웃
        </button>
      </div>

      <div className="bg-white border-b px-6 flex gap-4 overflow-x-auto">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
              tab === t.key ? 'border-[#1D9E75] text-[#1D9E75]' : 'border-transparent text-gray-500'
            }`}
          >
            {t.label}
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
              <p className="text-2xl font-bold">{metrics.ocr.success_rate_pct}%</p>
              <p className="text-xs text-gray-400 mt-1">총 {metrics.ocr.total}건 / 실패 {metrics.ocr.failed}건</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">LLM 성공률</p>
              <p className="text-2xl font-bold">{metrics.llm.success_rate_pct}%</p>
              <p className="text-xs text-gray-400 mt-1">총 {metrics.llm.total}건 / 실패 {metrics.llm.failed}건</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">P95 지연시간</p>
              <p className="text-2xl font-bold">{metrics.p95_latency_ms != null ? `${metrics.p95_latency_ms}ms` : '-'}</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm md:col-span-3">
              <p className="text-xs text-gray-500 mb-3">최근 7일 가이드 생성</p>
              <div className="flex items-end gap-2 h-24">
                {metrics.daily_guides.map(d => (
                  <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                    <div className="w-full rounded-t" style={{ background: '#1D9E75', height: `${Math.max(4, (d.guide_count / Math.max(...metrics.daily_guides.map(x => x.guide_count), 1)) * 80)}px` }} />
                    <p className="text-xs text-gray-400">{d.date.slice(5)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 모델 비교 */}
        {tab === 'comparison' && (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs">
                <tr>
                  <th className="px-4 py-3 text-left">버전</th>
                  <th className="px-4 py-3 text-left">평균 레이턴시</th>
                  <th className="px-4 py-3 text-left">성공률</th>
                  <th className="px-4 py-3 text-left">평균 평점</th>
                  <th className="px-4 py-3 text-left">총 건수</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map(c => (
                  <tr key={c.version} className="border-t border-gray-100">
                    <td className="px-4 py-3 font-medium">{c.version}</td>
                    <td className="px-4 py-3">{c.avg_latency_ms != null ? `${c.avg_latency_ms}ms` : '-'}</td>
                    <td className="px-4 py-3">{c.success_rate != null ? `${(c.success_rate * 100).toFixed(1)}%` : '-'}</td>
                    <td className="px-4 py-3">{c.avg_rating != null ? `${c.avg_rating} / 5` : '-'}</td>
                    <td className="px-4 py-3">{c.total_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 반복 테스트 */}
        {tab === 'consistency' && (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b">
              <p className="text-sm font-medium text-gray-700">동일 입력 반복 테스트 편차 분석</p>
              <p className="text-xs text-gray-400 mt-1">표준편차(stddev)가 낮을수록 결과 일관성이 높습니다</p>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs">
                <tr>
                  <th className="px-4 py-3 text-left">모델 타입</th>
                  <th className="px-4 py-3 text-left">평균 레이턴시</th>
                  <th className="px-4 py-3 text-left">표준편차</th>
                  <th className="px-4 py-3 text-left">샘플 수</th>
                  <th className="px-4 py-3 text-left">일관성</th>
                </tr>
              </thead>
              <tbody>
                {consistency.map(c => (
                  <tr key={c.model_type} className="border-t border-gray-100">
                    <td className="px-4 py-3 font-medium">{c.model_type}</td>
                    <td className="px-4 py-3">{c.mean_ms != null ? `${c.mean_ms}ms` : '-'}</td>
                    <td className="px-4 py-3">{c.stddev_ms != null ? `${c.stddev_ms}ms` : '-'}</td>
                    <td className="px-4 py-3">{c.sample_count}</td>
                    <td className="px-4 py-3">
                      {c.stddev_ms == null ? '-' : c.stddev_ms < 100 ? '✅ 안정' : c.stddev_ms < 500 ? '⚠️ 보통' : '❌ 불안정'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 피드백 흐름 */}
        {tab === 'feedback-flow' && feedbackFlow && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">총 피드백</p>
              <p className="text-2xl font-bold">{feedbackFlow.feedback_total}</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">긍정 피드백</p>
              <p className="text-2xl font-bold text-green-600">{feedbackFlow.positive_count}</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">부정 피드백</p>
              <p className="text-2xl font-bold text-red-500">{feedbackFlow.negative_count}</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm md:col-span-3">
              <p className="text-xs text-gray-500 mb-1">피드백 반영 구조</p>
              <p className="text-xs text-gray-600 mt-2 leading-relaxed">
                사용자 피드백 제출 → Feedback DB 저장 → MetricSnapshot 실시간 업데이트 → 일별 집계(Celery Beat) → 프롬프트 버전 개선
              </p>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 text-gray-400">
                    <tr>
                      <th className="px-3 py-2 text-left">날짜</th>
                      <th className="px-3 py-2 text-left">모델</th>
                      <th className="px-3 py-2 text-left">평균 평점</th>
                      <th className="px-3 py-2 text-left">성공률</th>
                    </tr>
                  </thead>
                  <tbody>
                    {feedbackFlow.improvement_trend.map((t, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="px-3 py-2">{t.date}</td>
                        <td className="px-3 py-2">{t.model_type}</td>
                        <td className="px-3 py-2">{t.avg_rating != null ? t.avg_rating : '-'}</td>
                        <td className="px-3 py-2">{t.success_rate != null ? `${(t.success_rate * 100).toFixed(1)}%` : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 테스트 보고서 */}
        {tab === 'report' && report && (
          <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
            <div className="border-b pb-4">
              <h2 className="text-lg font-bold text-gray-800">{report.title}</h2>
              <p className="text-xs text-gray-400 mt-1">생성일시: {report.generated_at}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">1. 피드백 요약</h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500">총 피드백</p>
                  <p className="text-xl font-bold">{report.summary.total_feedback}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500">긍정</p>
                  <p className="text-xl font-bold text-green-600">{report.summary.positive_feedback}</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-500">긍정률</p>
                  <p className="text-xl font-bold text-blue-600">{report.summary.positive_rate_pct}%</p>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">2. 모델 버전 비교</h3>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs">
                  <tr>
                    <th className="px-3 py-2 text-left">버전</th>
                    <th className="px-3 py-2 text-left">평균 평점</th>
                  </tr>
                </thead>
                <tbody>
                  {report.model_comparison.map(m => (
                    <tr key={m.version} className="border-t">
                      <td className="px-3 py-2">{m.version}</td>
                      <td className="px-3 py-2">{m.avg_rating != null ? `${m.avg_rating} / 5` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">3. 반복 테스트 일관성</h3>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs">
                  <tr>
                    <th className="px-3 py-2 text-left">모델</th>
                    <th className="px-3 py-2 text-left">평균 레이턴시</th>
                    <th className="px-3 py-2 text-left">표준편차</th>
                    <th className="px-3 py-2 text-left">샘플</th>
                  </tr>
                </thead>
                <tbody>
                  {report.consistency_analysis.map(c => (
                    <tr key={c.model_type} className="border-t">
                      <td className="px-3 py-2">{c.model_type}</td>
                      <td className="px-3 py-2">{c.mean_ms != null ? `${c.mean_ms}ms` : '-'}</td>
                      <td className="px-3 py-2">{c.stddev_ms != null ? `${c.stddev_ms}ms` : '-'}</td>
                      <td className="px-3 py-2">{c.sample_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">4. 비동기 처리 구조</h3>
              <p className="text-xs text-gray-600">{report.async_processing.description}</p>
              <div className="flex gap-2 mt-2 flex-wrap">
                {report.async_processing.queues.map(q => (
                  <span key={q} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">{q}</span>
                ))}
                {report.async_processing.workers.map(w => (
                  <span key={w} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">{w}</span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">5. 피드백 반영 구조</h3>
              <p className="text-xs text-gray-600">{report.feedback_structure.flow}</p>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded mt-2 inline-block">
                {report.feedback_structure.implemented ? '✅ 구현 완료' : '미구현'}
              </span>
            </div>
          </div>
        )}

        {/* 피드백 목록 */}
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
                {feedbacks.map((f: any) => (
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
                {users.map((u: any) => (
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