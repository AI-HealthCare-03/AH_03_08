import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageCircle, Plus } from 'lucide-react'
import { useChatSessions, useCreateSession, useGuides } from '@/entities/chatbot/api'
import { useMedicalRecords } from '@/entities/medical-record/api'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'
import { PageHeader } from '@/shared/ui/PageHeader'
import { EmptyState } from '@/shared/ui/EmptyState'
import { SkeletonList } from '@/shared/ui/SkeletonList'
import { SessionCard } from './SessionCard'
import { GuideSelectCard } from './GuideSelectCard'

interface SessionListProps {
  selectedSessionId?: string
}

export function SessionList({ selectedSessionId }: SessionListProps) {
  const navigate = useNavigate()
  const [showGuideSelector, setShowGuideSelector] = useState(false)

  const { data: sessions, isLoading: sessionsLoading } = useChatSessions()
  const { data: guides, isFetching: guidesFetching, refetch: refetchGuides } = useGuides()
  const { data: records } = useMedicalRecords()
  const { mutate: createSession, isPending } = useCreateSession()

  function handleSelectGuide(guideId: string) {
    const existingSession = sessions?.find((s) => s.guide_id === guideId)
    if (existingSession) {
      setShowGuideSelector(false)
      navigate(`/chatbot/${existingSession.id}`)
      return
    }

    const guide = guides?.find((g) => g.id === guideId)
    const record = records?.find((r) => r.id === guide?.record_id)
    const meta = record ? RECORD_TYPE_META[record.record_type] : null
    const placeName = record?.record_type === 'medicine_bag'
      ? record.parsed_data?.pharmacy
      : record?.parsed_data?.hospital
    const title = meta ? (placeName ? `${placeName} ${meta.label}` : meta.label) : '채팅 세션'

    createSession({ guide_id: guideId, title }, {
      onSuccess: (session) => {
        setShowGuideSelector(false)
        navigate(`/chatbot/${session.id}`)
      },
    })
  }

  if (sessionsLoading) return <SkeletonList count={3} />

  if (showGuideSelector) {
    if (guidesFetching) return <SkeletonList count={3} />
    const completedGuides = guides ?? []
    return (
      <div className="flex flex-col gap-4">
        <PageHeader
          title="의료기록 선택"
          description="채팅할 의료기록을 선택하세요."
          action={
            <button onClick={() => setShowGuideSelector(false)} className="text-sm text-gray-400 hover:text-gray-600">
              취소
            </button>
          }
        />
        {completedGuides.length === 0 ? (
          <EmptyState
            icon={<MessageCircle className="h-6 w-6" />}
            title="생성된 가이드가 없습니다"
            description="의료기록에서 가이드를 먼저 생성해주세요."
            action={{ label: '의료기록으로 이동', onClick: () => navigate('/medical-record') }}
          />
        ) : (
          <div className="flex flex-col gap-3">
            {completedGuides.map((guide) => {
              const record = records?.find((r) => r.id === guide.record_id)
              if (!record) return null
              return (
                <GuideSelectCard
                  key={guide.id}
                  record={record}
                  disabled={isPending}
                  onClick={() => handleSelectGuide(guide.id)}
                />
              )
            })}
          </div>
        )}
      </div>
    )
  }

  const hasSessions = (sessions?.length ?? 0) > 0

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="챗봇"
        description="처방전에 대해 궁금한 점을 물어보세요."
        action={
          hasSessions ? (
            <button
              onClick={() => { refetchGuides(); setShowGuideSelector(true) }}
              className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium text-white transition-opacity hover:opacity-80"
              style={{ background: '#1D9E75' }}
            >
              <Plus className="h-4 w-4" />
              새 채팅
            </button>
          ) : null
        }
      />
      {!hasSessions ? (
        <EmptyState
          icon={<MessageCircle className="h-6 w-6" />}
          title="아직 채팅이 없습니다"
          description="처방전 가이드를 선택해 첫 채팅을 시작해보세요."
          action={{ label: '채팅 시작', onClick: () => { refetchGuides(); setShowGuideSelector(true) } }}
        />
      ) : (
        <div className="flex flex-col gap-3">
          {sessions!.map((session) => {
            const guide = guides?.find((g) => g.id === session.guide_id)
            const record = records?.find((r) => r.id === guide?.record_id)
            return (
              <SessionCard
                key={session.id}
                session={session}
                isActive={session.id === selectedSessionId}
                medicationCount={record?.parsed_data?.medications?.length ?? 0}
                diseaseCode={record?.parsed_data?.disease_name ?? record?.parsed_data?.disease_code ?? null}
                onClick={() => navigate(`/chatbot/${session.id}`)}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
