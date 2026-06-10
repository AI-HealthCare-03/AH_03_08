import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GuideListScreen } from '@/features/guide/screens/GuideListScreen'
import { GuideDetailScreen } from '@/features/guide/screens/GuideDetailScreen'
import { useGuide, useGuides } from '@/entities/guide/api'

/**
 * 와이어프레임 플로우
 * - 모바일: 목록 화면 ↔ 상세 화면 (?id=)
 * - 데스크톱(lg+): 목록 + 상세 마스터-디테일
 */
export function GuidePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const guideId = searchParams.get('id')

  const {
    data: guides,
    isLoading: listLoading,
    isError: listError,
    error: listErrorDetail,
  } = useGuides()
  const listErrorMessage =
    listErrorDetail instanceof Error ? listErrorDetail.message : undefined
  const [selectedId, setSelectedId] = useState<string | null>(guideId)

  useEffect(() => {
    setSelectedId(guideId)
  }, [guideId])

  const { data: guide, isLoading: detailLoading } = useGuide(selectedId)

  function openDetail(id: string) {
    setSelectedId(id)
    setSearchParams({ id })
  }

  function backToList() {
    setSelectedId(null)
    setSearchParams({})
  }

  const showDetail = !!selectedId

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* 모바일: 목록 OR 상세 */}
      <div className="lg:hidden">
        {!showDetail ? (
          <GuideListScreen
            guides={guides}
            isLoading={listLoading}
            isError={listError}
            errorMessage={listErrorMessage}
            selectedId={null}
            onSelect={openDetail}
          />
        ) : (
          <GuideDetailScreen
            guide={guide}
            isLoading={detailLoading}
            showBack
            onBack={backToList}
          />
        )}
      </div>

      {/* 데스크톱: 목록 + 상세 */}
      <div className="hidden lg:grid lg:grid-cols-[minmax(300px,380px)_1fr] lg:gap-8 lg:items-start">
        <GuideListScreen
          guides={guides}
          isLoading={listLoading}
          isError={listError}
          errorMessage={listErrorMessage}
          selectedId={selectedId}
          onSelect={openDetail}
        />
        <div className="min-w-0 sticky top-8">
          {showDetail ? (
            <GuideDetailScreen guide={guide} isLoading={detailLoading} />
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-200 bg-gray-50/80 p-12 text-center">
              <p className="text-sm font-medium text-gray-600">왼쪽에서 가이드를 선택하세요</p>
              <p className="text-xs text-gray-400 mt-2">상세 내용이 이 영역에 표시됩니다</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
