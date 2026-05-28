import type { Guide } from '@/entities/guide/model'

export function formatGuideDate(iso: string | null | undefined): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function guideDisplayTitle(guide?: Guide): string {
  const title = guide?.title?.trim()
  if (title) return title
  const fromSummary = guide?.summary_text?.trim().slice(0, 15)
  if (fromSummary) return fromSummary
  return '맞춤 복약 가이드'
}

export function guideShortId(id: string): string {
  return `#${id.slice(0, 8)}`
}

/** 목록 카드 미리보기 (와이어프레임 스니펫) */
export function guidePreviewText(guide: Guide, maxLen = 72): string {
  const raw =
    guide.summary_text?.trim() ||
    guide.medication_guide?.trim() ||
    guide.lifestyle_guide?.trim() ||
    ''
  if (!raw) return '가이드 내용을 불러오는 중이거나 비어 있습니다.'
  const oneLine = raw.replace(/\s+/g, ' ')
  return oneLine.length <= maxLen ? oneLine : `${oneLine.slice(0, maxLen)}…`
}

export function splitBulletLines(text: string | null | undefined): string[] {
  if (!text?.trim()) return []
  return text
    .split(/\n+/)
    .map((line) => line.replace(/^[-•*]\s*/, '').trim())
    .filter(Boolean)
}
