import type { ParsedData, Medication } from '@/entities/medical-record/model'

interface ParsedDataFormProps {
  data: ParsedData
  onChange: (data: ParsedData) => void
}

export function ParsedDataForm({ data, onChange }: ParsedDataFormProps) {
  function setField(key: keyof Omit<ParsedData, 'medications'>, value: string) {
    onChange({ ...data, [key]: value || null })
  }

  function setMedField(index: number, key: keyof Medication, value: string) {
    const meds = [...(data.medications ?? [])]
    const numericKeys = new Set<keyof Medication>(['days', 'dosage', 'frequency'])
    const parsed = numericKeys.has(key) ? (value ? Number(value) : null) : value || null
    meds[index] = { ...meds[index], [key]: parsed }
    onChange({ ...data, medications: meds })
  }

  function addMed() {
    onChange({ ...data, medications: [...(data.medications ?? []), { name: '' }] })
  }

  function removeMed(index: number) {
    const meds = [...(data.medications ?? [])]
    meds.splice(index, 1)
    onChange({ ...data, medications: meds })
  }

  const meds = data.medications ?? []

  return (
    <div className="space-y-4 rounded-xl border border-gray-100 bg-white p-4">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <p className="text-sm font-semibold text-gray-900">기본 정보</p>
          <p className="text-xs text-blue-500">* 잘못된 정보가 있으면 수정해 주세요</p>
        </div>
        <div className="rounded-xl border border-gray-100 overflow-hidden">
          {(() => {
            const fields: { label: string; key: keyof Omit<ParsedData, 'medications'>; type: string }[] = [
              { label: '환자명', key: 'patient_name', type: 'text' },
              { label: '병원명', key: 'hospital', type: 'text' },
              { label: '약국명', key: 'pharmacy', type: 'text' },
              { label: '발행일', key: 'issued_at', type: 'date' },
              { label: '처방의', key: 'doctor', type: 'text' },
              { label: '약사명', key: 'pharmacist', type: 'text' },
            ]
            const rows: (typeof fields[number] | null)[][] = []
            for (let i = 0; i < fields.length; i += 2) rows.push([fields[i], fields[i + 1] ?? null])
            return rows.map((pair, ri) => {
              const hasSecond = pair[1] != null
              return (
                <div key={ri} className={`grid grid-cols-[5rem_1fr] md:grid-cols-[5rem_1fr_5rem_1fr] hover:bg-blue-50/40 transition-colors ${ri < rows.length - 1 ? 'border-b border-gray-100' : ''}`}>
                  {pair.map((f, ci) => f ? (
                    <>
                      <div
                        key={f.key + '-label'}
                        className={[
                          'px-3 py-2 text-xs font-medium text-gray-400 bg-gray-50 border-r border-gray-100 flex items-center',
                          ci === 0 && hasSecond ? 'border-b border-gray-100 md:border-b-0' : '',
                          ci === 1 ? 'md:border-l border-gray-100' : '',
                        ].join(' ')}
                      >
                        {f.label}
                      </div>
                      <div
                        key={f.key + '-val'}
                        className={[
                          'px-3 py-2 flex items-center',
                          ci === 0 && hasSecond ? 'border-b border-gray-100 md:border-b-0' : '',
                          ci === 0 ? 'md:border-r border-gray-100' : '',
                        ].join(' ')}
                      >
                        {f.type === 'date' ? (
                          <input
                            type="date"
                            className="w-full bg-transparent text-sm text-gray-800 outline-none focus:bg-white focus:rounded focus:px-1 transition-all"
                            value={toDateInputValue(data[f.key] as string ?? '')}
                            onChange={(e) => setField(f.key, e.target.value)}
                          />
                        ) : (
                          <TableCell value={data[f.key] as string ?? ''} onChange={(v) => setField(f.key, v)} />
                        )}
                      </div>
                    </>
                  ) : (
                    <><div key="empty-label" className="md:border-l border-gray-100 bg-gray-50" /><div key="empty-val" /></>
                  ))}
                </div>
              )
            })
          })()}
        </div>
      </div>

      <div>
        <p className="mb-2 text-sm font-semibold text-gray-900">진단 정보</p>
        <div className="rounded-xl border border-gray-100 overflow-hidden">
          <div className="grid grid-cols-[5rem_1fr] hover:bg-blue-50/40 transition-colors">
            <div className="px-3 py-2 text-xs font-medium text-gray-400 bg-gray-50 border-r border-gray-100 flex items-center">분류기호</div>
            <div className="px-3 py-2 flex items-center">
              <TableCell value={data.disease_code ?? ''} onChange={(v) => setField('disease_code', v)} />
            </div>
          </div>
        </div>
      </div>

      <div>
        <div className="mb-2">
          <p className="text-sm font-semibold text-gray-900">의약품 ({meds.length}개)</p>
        </div>
        <div className="rounded-xl border border-gray-100 overflow-hidden">
          {/* 헤더 */}
          <div className="grid grid-cols-[2fr_0.8fr_0.6fr_0.6fr_0.6fr_1.2rem] md:grid-cols-[2fr_0.8fr_0.6fr_0.6fr_0.6fr_1.5fr_1.2rem] bg-gray-50 border-b border-gray-100">
            {['약품명', '함량', '용량', '횟수', '일수'].map((h) => (
              <div key={h} className="px-3 py-2 text-xs font-semibold text-gray-400">{h}</div>
            ))}
            <div className="hidden md:block px-3 py-2 text-xs font-semibold text-gray-400">용법</div>
            <div />
          </div>
          {/* 행 */}
          {meds.map((med, i) => (
            <div key={i} className={`grid grid-cols-[2fr_0.8fr_0.6fr_0.6fr_0.6fr_1.2rem] md:grid-cols-[2fr_0.8fr_0.6fr_0.6fr_0.6fr_1.5fr_1.2rem] hover:bg-blue-50/40 transition-colors ${i < meds.length - 1 ? 'border-b border-gray-100' : ''}`}>
              <div className={`px-2 py-2 border-r border-gray-100 ${!med.name ? 'animate-pulse bg-red-50' : ''}`}>
                {med.drug_class && (
                  <span className="inline-block mb-1 text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: '#E1F5EE', color: '#0F6E56' }}>
                    {med.drug_class}
                  </span>
                )}
                <TableCell value={med.name ?? ''} onChange={(v) => setMedField(i, 'name', v)} />
                {/* 모바일 전용 서브행 */}
                <div className="md:hidden mt-1 flex items-center gap-1">
                  <span className="shrink-0 text-[9px] text-gray-300">용법</span>
                  <TableCell
                    value={med.instructions != null ? String(med.instructions) : ''}
                    onChange={(v) => setMedField(i, 'instructions', v)}
                  />
                </div>
              </div>
              <div className="px-2 py-2 border-r border-gray-100 flex items-center">
                <TableCell value={med.concentration ?? ''} onChange={(v) => setMedField(i, 'concentration', v)} />
              </div>
              <div className={`px-2 py-2 border-r border-gray-100 flex items-center ${!med.dosage ? 'animate-pulse bg-red-50' : ''}`}>
                <TableCell value={med.dosage != null ? String(med.dosage) : ''} onChange={(v) => setMedField(i, 'dosage', v)} />
              </div>
              <div className={`px-2 py-2 border-r border-gray-100 flex items-center ${!med.frequency ? 'animate-pulse bg-red-50' : ''}`}>
                <TableCell value={med.frequency != null ? String(med.frequency) : ''} onChange={(v) => setMedField(i, 'frequency', v)} />
              </div>
              <div className={`px-2 py-2 border-r border-gray-100 flex items-center ${med.days == null ? 'animate-pulse bg-red-50' : ''}`}>
                <TableCell value={med.days != null ? String(med.days) : ''} onChange={(v) => setMedField(i, 'days', v)} />
              </div>
              {/* 데스크탑 전용 용법 열 */}
              <div className="hidden md:flex px-2 py-2 border-r border-gray-100 items-center">
                <TableCell
                  value={med.instructions != null ? String(med.instructions) : ''}
                  onChange={(v) => setMedField(i, 'instructions', v)}
                />
              </div>
              <div className="flex items-center justify-center">
                <button type="button" onClick={() => removeMed(i)}
                  className="p-0.5 rounded text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors">
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
          {/* 행 추가 */}
          <button
            type="button"
            onClick={addMed}
            className="w-full flex items-center justify-center gap-1 py-2 border-t border-dashed border-gray-200 text-xs text-gray-400 hover:text-primary hover:bg-blue-50/40 transition-colors"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
            </svg>
            약품 추가
          </button>
        </div>
      </div>
    </div>
  )
}

function TableCell({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <input
      className="w-full bg-transparent text-sm text-gray-800 outline-none placeholder:text-gray-300 cursor-text rounded-none border-b border-transparent hover:border-dashed hover:border-gray-300 focus:border-solid focus:border-primary focus:bg-white focus:px-1 transition-all"
      value={value}
      placeholder="—"
      onChange={(e) => onChange(e.target.value)}
    />
  )
}

function toDateInputValue(val: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(val)) return val
  const dot = val.match(/^(\d{4})[./](\d{1,2})[./](\d{1,2})$/)
  if (dot) return `${dot[1]}-${dot[2].padStart(2, '0')}-${dot[3].padStart(2, '0')}`
  return ''
}

