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
    const parsed = key === 'days' ? (value ? Number(value) : null) : value || null
    meds[index] = { ...meds[index], [key]: parsed }
    onChange({ ...data, medications: meds })
  }

  const meds = data.medications ?? []

  return (
    <div className="space-y-4 rounded-xl border border-gray-100 bg-white p-4">
      <div>
        <p className="mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wide">기본 정보</p>
        <div className="grid grid-cols-2 gap-3">
          <Field label="환자명" value={data.patient_name ?? ''} onChange={(v) => setField('patient_name', v)} />
          <Field label="병원명" value={data.hospital ?? ''} onChange={(v) => setField('hospital', v)} />
          <Field label="약국명" value={data.pharmacy ?? ''} onChange={(v) => setField('pharmacy', v)} />
          <DateField label="발행일" value={data.issued_at ?? ''} onChange={(v) => setField('issued_at', v)} />
          <Field label="처방의" value={data.doctor ?? ''} onChange={(v) => setField('doctor', v)} />
          <Field label="약사명" value={data.pharmacist ?? ''} onChange={(v) => setField('pharmacist', v)} />
        </div>
      </div>

      {meds.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wide">의약품 ({meds.length}개)</p>
          <div className="space-y-3">
            {meds.map((med, i) => (
              <div key={i} className="rounded-xl border border-gray-100 bg-[#F5F5F4] p-3">
                <div className="grid grid-cols-2 gap-2">
                  <Field label="약품명" value={med.name ?? ''} onChange={(v) => setMedField(i, 'name', v)} />
                  <Field label="용량" value={med.dosage ?? ''} onChange={(v) => setMedField(i, 'dosage', v)} />
                  <Field label="일 투여횟수" value={med.frequency ?? ''} onChange={(v) => setMedField(i, 'frequency', v)} />
                  <Field label="복용일수" value={med.days != null ? String(med.days) : ''} onChange={(v) => setMedField(i, 'days', v)} />
                </div>
                {med.instructions && (
                  <p className="mt-2 text-xs text-gray-500">{med.instructions}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-500">{label}</label>
      <input
        className="w-full rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-800 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

function toDateInputValue(val: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(val)) return val
  const dot = val.match(/^(\d{4})[./](\d{1,2})[./](\d{1,2})$/)
  if (dot) return `${dot[1]}-${dot[2].padStart(2, '0')}-${dot[3].padStart(2, '0')}`
  return ''
}

function DateField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-500">{label}</label>
      <input
        type="date"
        className="w-full rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-800 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
        value={toDateInputValue(value)}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}
