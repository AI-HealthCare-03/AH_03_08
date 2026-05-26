import { useMemo, useState } from 'react'
import { AlertTriangle, HeartPulse, Paperclip, Pill } from 'lucide-react'
import type { Guide } from '@/entities/guide/model'
import { GUIDE_TABS, type GuideContentTab } from './constants'
import { splitBulletLines } from './guide-utils'
import { useRecord } from '@/entities/medical-record/api'

interface GuideContentTabsProps {
  guide: Guide
}

function WarningBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-amber-200 bg-status-amber-bg px-4 py-3 flex gap-2">
      <AlertTriangle className="h-5 w-5 shrink-0 text-status-amber-icon mt-0.5" />
      <div className="text-sm text-status-amber-text leading-relaxed">{children}</div>
    </div>
  )
}

/** 와이어프레임 — 복약 / 생활 / 정보 조회 탭 */
export function GuideContentTabs({ guide }: GuideContentTabsProps) {
  const [tab, setTab] = useState<GuideContentTab>('medication')
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
                const meta = [m.frequency, m.instructions].filter(Boolean).join(' · ')
                return (
                  <article key={m.name} className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <span className="inline-flex items-center rounded-lg bg-brand-lightest px-2 py-1 text-xs font-semibold text-brand-dark">
                          {m.name}{m.dosage ? ` ${m.dosage}` : ''}
                        </span>
                      </div>
                      {meta && <p className="text-xs font-medium text-gray-500">{meta}</p>}
                    </div>
                    <p className="mt-3 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                      {m.instructions?.trim() || guide.medication_guide?.trim() || ''}
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
                {guide.medication_guide?.trim() || '복약 안내 내용이 없습니다.'}
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
          {splitBulletLines(guide.lifestyle_guide).length > 0 ? (
            <ul className="space-y-2 text-sm text-gray-700 list-disc pl-5">
              {splitBulletLines(guide.lifestyle_guide).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {guide.lifestyle_guide?.trim() || '생활 가이드 내용이 없습니다.'}
            </p>
          )}
        </article>
      )}

      {tab === 'info' && (
        <div className="space-y-4">
          <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Paperclip className="h-5 w-5 text-brand-primary" />
              <h3 className="text-sm font-semibold text-gray-900">첨부 자료</h3>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">
              TTS / 카드 이미지 자산은 준비 중입니다. (요청 버튼은 상단에서 동작)
            </p>
          </article>

          {guide.allergy_warnings && guide.allergy_warnings.length > 0 && (
            <div className="rounded-2xl border border-red-100 bg-status-red-bg/60 p-4 space-y-2">
              <p className="text-sm font-semibold text-status-red-text">알러지 경고</p>
              {guide.allergy_warnings.map((w) => (
                <p key={`${w.drug_name}-${w.warning}`} className="text-sm text-status-red-text">
                  <span className="font-medium">{w.drug_name}</span>: {w.warning}
                </p>
              ))}
            </div>
          )}

          {guide.condition_interactions && guide.condition_interactions.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                기저질환 상호작용
              </p>
              {guide.condition_interactions.map((c) => (
                <WarningBox key={`${c.drug_name}-${c.condition}`}>
                  <span className="font-medium">{c.drug_name}</span> · {c.condition}: {c.interaction}
                </WarningBox>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
