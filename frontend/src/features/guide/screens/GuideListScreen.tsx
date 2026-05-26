import type { Guide } from '@/entities/guide/model'
import { GuideListCard } from '../GuideListCard'
import { EmptyState } from '@/shared/ui/EmptyState'
import { SkeletonList } from '@/shared/ui/SkeletonList'

interface GuideListScreenProps {
  guides: Guide[] | undefined
  isLoading: boolean
  isError?: boolean
  errorMessage?: string
  selectedId: string | null
  onSelect: (id: string) => void
}

/** 와이어프레임 — 가이드 목록 화면 */
export function GuideListScreen({
  guides,
  isLoading,
  isError,
  errorMessage,
  selectedId,
  onSelect,
}: GuideListScreenProps) {
  return (
    <div className="flex flex-col gap-5">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">가이드 목록</h1>
        <p className="text-sm text-gray-500">AI가 생성한 복약 가이드</p>
      </header>

      {isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <p className="font-medium">가이드 목록을 불러오지 못했습니다.</p>
          <p className="mt-1 text-red-700/90 text-xs leading-relaxed">
            {errorMessage ??
              '로그인 상태와 API(localhost:8000) 실행 여부를 확인해 주세요. DB 마이그레이션 미적용 시에도 실패할 수 있습니다.'}
          </p>
        </div>
      )}

      {isLoading && <SkeletonList count={4} className="h-[120px]" />}

      {!isLoading && !isError && !guides?.length && (
        <EmptyState
          title="가이드가 없습니다"
          description="의료기록에서 OCR 완료 후 가이드 생성을 요청해 주세요."
        />
      )}

      {!isLoading && guides && guides.length > 0 && (
        <ul className="space-y-3">
          {guides.map((guide) => (
            <li key={guide.id}>
              <GuideListCard
                guide={guide}
                selected={selectedId === guide.id}
                onSelect={() => onSelect(guide.id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
