import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const STATS = [
  { value: 'CLOVA OCR', label: '의료 특화 OCR 엔진' },
  { value: 'GPT-4o', label: 'LLM 복약 가이드 생성' },
  { value: '실시간', label: 'WebSocket 챗봇 스트리밍' },
  { value: '자동화', label: '복약 캘린더·알림 생성' },
]

const FEATURES = [
  {
    tag: 'OCR 의료정보 인식',
    title: '처방전·약봉투를 찍으면\nAI가 알아서 분석해요',
    desc: '이미지나 PDF를 업로드하면 CLOVA OCR이 텍스트를 추출하고,\nGPT가 약품명·용법·용량·질병분류기호를 자동으로 정리합니다.\n추출된 내용은 직접 확인하고 수정할 수 있어요.',
    points: ['처방전·약봉투·진료기록 지원', 'KCD 질병분류기호 자동 추출 및 정규화', '추출 결과 직접 확인·수정 가능'],
    imageAlt: 'OCR 업로드 화면',
    reverse: false,
  },
  {
    tag: 'LLM 복약 가이드',
    title: '내 처방에 맞는\n복약 가이드를 자동 생성해요',
    desc: 'RAG 기반 의약품 데이터베이스와 GPT가 결합하여\n복용법·주의사항·약물 상호작용·알레르기 경고까지\n항목별로 이해하기 쉽게 정리해 드립니다.',
    points: ['약물 상호작용·부작용 경고', '생활습관 개선 가이드 포함', '알레르기·기저질환 정보 반영'],
    imageAlt: '복약 가이드 화면',
    reverse: true,
  },
  {
    tag: '실시간 AI 챗봇',
    title: '내 처방 내용을 이해하는\nAI와 대화하세요',
    desc: '챗봇은 업로드한 처방전 내용을 기억하고 있어요.\n약 복용 시간, 부작용, 주의사항 등 궁금한 것을\n언제든지 실시간으로 물어볼 수 있습니다.',
    points: ['처방전 컨텍스트 기반 맞춤 답변', '대화 히스토리 세션별 저장·복원', '위험 정보는 경고 마커로 구분 표시'],
    imageAlt: '챗봇 대화 화면',
    reverse: false,
  },
  {
    tag: '복약 캘린더·알림',
    title: '복약 일정을 자동으로\n관리해 드려요',
    desc: '처방 기간에 맞춰 복약 캘린더가 자동으로 생성되고,\n설정한 시간에 알림을 보내드립니다.\n복용 완료·미복용 여부도 손쉽게 기록할 수 있어요.',
    points: ['처방 기간 내 일정 자동 생성', '복용 완료·미복용 상태 관리', '알림 시간 직접 설정 가능'],
    imageAlt: '복약 캘린더 화면',
    reverse: true,
  },
]

const STEPS = [
  {
    step: '01',
    title: '의료기록 업로드',
    desc: '처방전·약봉투 사진이나 PDF를 업로드하세요. AI가 자동으로 분석을 시작합니다.',
  },
  {
    step: '02',
    title: '복약 가이드 확인',
    desc: '내 처방에 맞게 생성된 복약 가이드를 확인하고, 챗봇으로 궁금한 점을 바로 물어보세요.',
  },
  {
    step: '03',
    title: '캘린더로 관리',
    desc: '자동 생성된 복약 일정을 캘린더에서 확인하고 알림으로 복약을 챙기세요.',
  },
]

export function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* 헤더 */}
      <header className="sticky top-0 z-50 flex items-center justify-between px-6 md:px-16 h-16 border-b border-gray-100 bg-white/90 backdrop-blur-sm">
        <span className="text-xl font-bold" style={{ color: '#1D9E75' }}>메디로그</span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate('/auth/login')}>
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
      <section className="flex flex-col lg:flex-row items-center justify-between px-6 md:px-16 py-20 md:py-28 gap-12 max-w-6xl mx-auto w-full">
        <div className="flex-1 text-left">
          <div
            className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-medium mb-6"
            style={{ background: '#E1F5EE', color: '#0F6E56' }}
          >
            AI 기반 복약 관리 서비스
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight mb-5">
            내 처방전,<br />
            <span style={{ color: '#1D9E75' }}>AI가 읽어드립니다</span>
          </h1>
          <p className="text-base md:text-lg text-gray-500 mb-8 max-w-md leading-relaxed">
            처방전과 약봉투를 업로드하면 OCR이 정보를 추출하고,
            LLM이 맞춤형 복약 가이드를 자동으로 생성합니다.
            AI 챗봇으로 언제든지 질문하고, 캘린더로 복약을 관리하세요.
          </p>
          <div className="flex gap-3">
            <Button
              size="lg"
              className="px-8 text-white"
              style={{ background: '#1D9E75' }}
              onClick={() => navigate('/auth/register')}
            >
              무료로 시작하기
            </Button>
            <Button variant="outline" size="lg" className="px-8" onClick={() => navigate('/auth/login')}>
              로그인
            </Button>
          </div>
        </div>

        {/* 히어로 이미지 */}
        <div className="flex-1 w-full max-w-lg">
          <div className="rounded-2xl overflow-hidden shadow-2xl border border-gray-100 bg-gray-50 aspect-[4/3] flex items-center justify-center">
            <img
              src="/images/landing-hero.png"
              alt="메디로그 서비스 화면"
              className="w-full h-full object-cover"
              onError={(e) => {
                const el = e.currentTarget
                el.style.display = 'none'
                el.parentElement!.innerHTML = '<span class="text-gray-300 text-sm">서비스 화면 이미지</span>'
              }}
            />
          </div>
        </div>
      </section>

      {/* Stats 바 */}
      <section className="border-y border-gray-100 bg-gray-50 py-10">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-xl font-bold mb-1" style={{ color: '#1D9E75' }}>{s.value}</div>
              <div className="text-xs text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 기능 상세 섹션 */}
      <section className="py-8">
        {FEATURES.map((f, i) => (
          <div
            key={f.tag}
            className={`flex flex-col ${f.reverse ? 'lg:flex-row-reverse' : 'lg:flex-row'} items-center gap-12 px-6 md:px-16 py-16 max-w-6xl mx-auto`}
          >
            {/* 이미지 */}
            <div className="flex-1 w-full max-w-lg">
              <div
                className="rounded-2xl overflow-hidden shadow-lg border border-gray-100 bg-gray-50 aspect-[4/3] flex items-center justify-center"
                style={{ background: i % 2 === 0 ? '#F0FAF6' : '#F5F5F4' }}
              >
                <img
                  src={`/images/feature-${i + 1}.png`}
                  alt={f.imageAlt}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const el = e.currentTarget
                    el.style.display = 'none'
                    el.parentElement!.innerHTML = `<span class="text-gray-300 text-sm">${f.imageAlt}</span>`
                  }}
                />
              </div>
            </div>

            {/* 텍스트 */}
            <div className="flex-1">
              <span
                className="inline-block text-xs font-semibold rounded-full px-3 py-1 mb-4"
                style={{ background: '#E1F5EE', color: '#0F6E56' }}
              >
                {f.tag}
              </span>
              <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4 leading-snug whitespace-pre-line">
                {f.title}
              </h2>
              <p className="text-sm text-gray-500 leading-relaxed mb-6 whitespace-pre-line">
                {f.desc}
              </p>
              <ul className="space-y-2">
                {f.points.map((p) => (
                  <li key={p} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="mt-0.5 shrink-0" style={{ color: '#1D9E75' }}>✓</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </section>

      {/* 사용 흐름 */}
      <section className="py-20 px-6 md:px-16" style={{ background: '#F5F5F4' }}>
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 text-center mb-4">
            3단계로 시작하세요
          </h2>
          <p className="text-sm text-gray-500 text-center mb-14">
            복잡한 설정 없이 업로드 한 번으로 모든 기능을 이용할 수 있어요.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((s, i) => (
              <div key={s.step} className="relative">
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-6 left-full w-full h-px bg-gray-200 z-0" style={{ width: 'calc(100% - 3rem)', left: '4rem' }} />
                )}
                <div className="bg-white rounded-2xl p-6 shadow-sm relative z-10">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white mb-4"
                    style={{ background: '#1D9E75' }}
                  >
                    {s.step}
                  </div>
                  <h3 className="text-base font-semibold text-gray-900 mb-2">{s.title}</h3>
                  <p className="text-xs text-gray-500 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 하단 CTA */}
      <section className="py-24 px-6 text-center" style={{ background: '#1D9E75' }}>
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
          지금 바로 시작해보세요
        </h2>
        <p className="text-sm text-green-100 mb-8">
          처방전 하나로 복약 관리의 모든 것을 경험하세요.
        </p>
        <Button
          size="lg"
          className="px-10 font-semibold bg-white hover:bg-gray-50"
          style={{ color: '#1D9E75' }}
          onClick={() => navigate('/auth/register')}
        >
          무료로 시작하기
        </Button>
      </section>

      {/* 푸터 */}
      <footer className="text-center py-8 text-xs text-gray-400 border-t border-gray-100">
        © 2025 메디로그. All rights reserved.
      </footer>
    </div>
  )
}
