import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const FEATURES = [
  {
    icon: '📋',
    title: '의료기록 업로드',
    desc: '처방전·약봉투·낱알 사진을 올리면 AI가 자동으로 분석합니다.',
  },
  {
    icon: '💊',
    title: '복약 가이드',
    desc: '내 약에 맞는 복용법·주의사항을 알기 쉽게 정리해 드립니다.',
  },
  {
    icon: '🤖',
    title: 'AI 챗봇 상담',
    desc: '궁금한 점을 언제든지 물어보세요. 24시간 답변합니다.',
  },
  {
    icon: '🔔',
    title: '복약 알림',
    desc: '캘린더와 연동해 복약 시간을 놓치지 않도록 알려드립니다.',
  },
]

export function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--color-background-primary)' }}>
      {/* 헤더 */}
      <header className="flex items-center justify-between px-6 md:px-12 h-16 border-b border-gray-100">
        <span className="text-xl font-bold" style={{ color: '#1D9E75' }}>메디로그</span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/auth/login')}
          >
            로그인
          </Button>
          <Button
            size="sm"
            className="text-white"
            style={{ background: '#1D9E75' }}
            onClick={() => navigate('/auth/register')}
          >
            회원가입
          </Button>
        </div>
      </header>

      {/* 히어로 */}
      <section className="flex flex-col items-center justify-center text-center px-6 py-24 md:py-36 flex-1">
        <div
          className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-medium mb-6"
          style={{ background: '#E1F5EE', color: '#0F6E56' }}
        >
          AI 기반 건강 기록 관리
        </div>

        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight mb-4">
          내 약, 제대로 알고<br />
          <span style={{ color: '#1D9E75' }}>올바르게 복용하세요</span>
        </h1>

        <p className="text-base md:text-lg text-gray-500 max-w-md mb-10">
          처방전과 약봉투를 업로드하면 AI가 분석해 맞춤 복약 가이드를 제공합니다.
        </p>

        <div className="flex gap-3">
          <Button
            size="lg"
            className="px-8 text-white"
            style={{ background: '#1D9E75' }}
            onClick={() => navigate('/auth/register')}
          >
            회원가입
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="px-8"
            onClick={() => navigate('/auth/login')}
          >
            로그인
          </Button>
        </div>
      </section>

      {/* 기능 소개 */}
      <section className="px-6 md:px-12 py-16" style={{ background: '#F5F5F4' }}>
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-10">주요 기능</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-5xl mx-auto">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-white rounded-2xl p-6 shadow-sm"
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="text-sm font-semibold text-gray-800 mb-1">{f.title}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 푸터 */}
      <footer className="text-center py-6 text-xs text-gray-400 border-t border-gray-100">
        © 2025 메디로그. All rights reserved.
      </footer>
    </div>
  )
}
