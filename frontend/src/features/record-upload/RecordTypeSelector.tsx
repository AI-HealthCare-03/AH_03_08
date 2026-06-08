import type { RecordType } from '@/shared/types'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'

interface RecordTypeSelectorProps {
  selected: RecordType | null
  onChange: (type: RecordType) => void
}

export function RecordTypeSelector({ selected, onChange }: RecordTypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {(Object.entries(RECORD_TYPE_META) as [RecordType, typeof RECORD_TYPE_META[RecordType]][]).map(
        ([type, meta]) => (
          <button
            key={type}
            type="button"
            onClick={() => onChange(type)}
            className={`flex items-center gap-4 rounded-xl border-2 p-4 text-left transition-all ${
              selected === type
                ? 'border-primary bg-[#E8F5EE]'
                : 'border-gray-100 bg-white hover:border-gray-200'
            }`}
          >
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
              selected === type ? 'bg-primary/15' : 'bg-gray-100'
            }`}>
              <RecordTypeIcon name={meta.icon} active={selected === type} />
            </div>
            <div>
              <p className={`text-sm font-bold ${selected === type ? 'text-primary' : 'text-gray-900'}`}>
                {meta.label}
              </p>
              <p className="text-xs text-gray-400 leading-tight mt-0.5">{meta.description}</p>
            </div>
          </button>
        ),
      )}
    </div>
  )
}

function RecordTypeIcon({ name, active }: { name: string; active: boolean }) {
  const color = active ? '#4a9b6f' : '#9ca3af'
  const paths: Record<string, React.ReactNode> = {
    'file-text': (
      <>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M9 12h6M9 16h6M7 4H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2h-2" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 4h6v2H9V4z" />
      </>
    ),
    package: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    ),
    camera: (
      <>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="m8.5 8.5 7 7" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2}
          d="M 15.5 5 A 3 3 0 0 1 19 8.5" />
      </>
    ),
  }
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke={color}>
      {paths[name]}
    </svg>
  )
}
