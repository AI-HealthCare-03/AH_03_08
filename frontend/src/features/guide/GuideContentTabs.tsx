import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Download, HeartPulse, Newspaper, Pill } from 'lucide-react'
import type { Guide } from '@/entities/guide/model'
import { GUIDE_TABS, type GuideContentTab } from './constants'
import { splitBulletLines } from './guide-utils'
import { useRecord } from '@/entities/medical-record/api'
import { toast } from '@/shared/lib/toast'
import { apiClient } from '@/shared/api/client'

interface GuideContentTabsProps {
  guide: Guide
}

function toStr(val: unknown): string {
  if (!val) return ''
  if (Array.isArray(val)) return (val as string[]).join('\n')
  if (typeof val === 'object') {
    const obj = val as Record<string, unknown>
    if (obj.raw && typeof obj.raw === 'string') return obj.raw
    return Object.values(obj).filter(v => typeof v === 'string').join('\n')
  }
  return String(val)
}

function WarningBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-amber-200 bg-status-amber-bg px-4 py-3 flex gap-2">
      <AlertTriangle className="h-5 w-5 shrink-0 text-status-amber-icon mt-0.5" />
      <div className="text-sm text-status-amber-text leading-relaxed">{children}</div>
    </div>
  )
}

export function GuideContentTabs({ guide }: GuideContentTabsProps) {
  const [tab, setTab] = useState<GuideContentTab>('medication')
  const [isCardNewsLoading, setIsCardNewsLoading] = useState(false)
  const [cardNewsUrl, setCardNewsUrl] = useState<string | null>(null)

  useEffect(() => {
    setTab('medication')
    setCardNewsUrl(null)
  }, [guide.id])

  const { data: record } = useRecord(guide.record_id)
  const meds = record?.parsed_data?.medications ?? []

  const warningsByDrug = useMemo(() => {
    const map = new Map<string, string[]>()
    for (const w of guide.allergy_warnings ?? []) {
      const key = w.drug_name
      map.set(key, [...(map.get(key) ?? []), w.warning])
    }
    for (const c of guide.condition_interactions ?? []) {
      const key = c.drug_name
      map.set(key, [...(map.get(key) ?? []), `${c.condition}: ${c.interaction}`])
    }
    return map
  }, [guide.allergy_warnings, guide.condition_interactions])

  const primaryWarning =
    guide.condition_interactions?.[0] ||
    (guide.allergy_warnings?.[0]
      ? {
          drug_name: guide.allergy_warnings[0].drug_name,
          condition: '알러지',
          interaction: guide.allergy_warnings[0].warning,
        }
      : null)

  async function handleCreateCardNews() {
    try {
      setIsCardNewsLoading(true)
      const response = await apiClient.post(
        `/guides/${guide.id}/assets`,
        { asset_type: 'card_news' },
        { responseType: 'blob' },
      )
      const url = URL.createObjectURL(response.data)
      setCardNewsUrl(url)
      toast.success('카드뉴스가 생성되었습니다.')
    } catch {
      toast.error('카드뉴스 생성 요청에 실패했습니다.')
    } finally {
      setIsCardNewsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex border-b border-gray-200 overflow-x-auto">
        {GUIDE_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`shrink-0 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.id
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'medication' && (
        <div className="space-y-4">
          {meds.length > 0 ? (
            <div className="space-y-4">
              {meds.map((m) => {
                const warn = warningsByDrug.get(m.name)?.[0]
                return (
                  <article key={m.name} className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <span className="inline-flex items-center rounded-lg bg-brand-lightest px-2 py-1 text-xs font-semibold text-brand-dark">
                          {m.name}{m.dosage ? ` ${m.dosage}` : ''}
                        </span>
                      </div>
                      {m.frequency && (
                        <span className="inline-flex items-center rounded-full bg-brand-lightest px-2.5 py-1 text-xs font-medium text-brand-dark">
                          하루 {m.frequency}회
                        </span>
                      )}
                    </div>
                    <p className="mt-3 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                      {(() => {
                        const full = toStr(guide.medication_guide).trim()
                        const sections = full.split(/■\s*/).filter(Boolean)
                        const matched = sections.find(s => s.startsWith(m.name)) ?? sections[0] ?? full
                        return matched.replace(m.name, '').trim()
                      })()}
                    </p>
                    {warn && (
                      <div className="mt-4 rounded-xl bg-status-amber-bg px-4 py-3">
                        <p className="text-xs font-semibold text-status-amber-text mb-1">⚠️ 주의사항</p>
                        <p className="text-sm text-status-amber-text leading-relaxed">{warn}</p>
                      </div>
                    )}
                  </article>
                )
              })}
            </div>
          ) : (
            <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <Pill className="h-5 w-5 text-brand-primary" />
                <h3 className="text-sm font-semibold text-gray-900">복약 안내</h3>
              </div>
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                {toStr(guide.medication_guide).trim() || '복약 안내 내용이 없습니다.'}
              </p>
            </article>
          )}
          {primaryWarning && (
            <WarningBox>
              <span className="font-semibold">주의: </span>
              {primaryWarning.drug_name}
              {primaryWarning.condition ? ` · ${primaryWarning.condition}` : ''}:{' '}
              {primaryWarning.interaction}
            </WarningBox>
          )}
        </div>
      )}

      {tab === 'lifestyle' && (
        <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <HeartPulse className="h-5 w-5 text-brand-primary" />
            <h3 className="text-sm font-semibold text-gray-900">생활습관 가이드</h3>
          </div>
          {splitBulletLines(toStr(guide.lifestyle_guide)).length > 0 ? (
            <ul className="space-y-2 text-sm text-gray-700 list-disc pl-5">
              {splitBulletLines(toStr(guide.lifestyle_guide)).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {toStr(guide.lifestyle_guide).trim() || '생활 가이드 내용이 없습니다.'}
            </p>
          )}
        </article>
      )}

      {tab === 'info' && (
        <div className="space-y-4">
          <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Newspaper className="h-5 w-5 text-brand-primary" />
              <h3 className="text-sm font-semibold text-gray-900">카드뉴스</h3>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleCreateCardNews}
                disabled={isCardNewsLoading}
                className="flex-1 rounded-xl border-2 border-dashed border-brand-primary py-4 text-sm font-semibold text-brand-primary hover:bg-brand-lightest transition-colors disabled:opacity-50"
              >
                {isCardNewsLoading ? '생성 중...' : cardNewsUrl ? '카드뉴스 재생성' : '카드뉴스 생성'}
              </button>
              {cardNewsUrl && (
                <button
                  type="button"
                  onClick={() => {
                    const now = new Date()
                    const date = `${String(now.getFullYear()).slice(2)}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
                    const a = document.createElement('a')
                    a.href = cardNewsUrl
                    a.download = `medilog_guide_${date}.png`
                    a.click()
                  }}
                  className="flex items-center gap-1.5 rounded-xl bg-brand-primary px-4 py-4 text-sm font-semibold text-white hover:opacity-90 transition-opacity"
                >
                  <Download className="h-4 w-4" />
                  저장
                </button>
              )}
            </div>
            {cardNewsUrl && (
              <img
                src={cardNewsUrl}
                alt="카드뉴스"
                className="mt-4 w-full rounded-xl border border-gray-100"
              />
            )}
          </article>
        </div>
      )}
    </div>
  )
}
