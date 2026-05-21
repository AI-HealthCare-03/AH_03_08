import type { RecordType } from '@/shared/types'
import { RECORD_TYPE_META } from '@/entities/medical-record/model'

interface RecordTypeSelectorProps {
  selected: RecordType | null
  onChange: (type: RecordType) => void
}

export function RecordTypeSelector({ selected, onChange }: RecordTypeSelectorProps) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {(Object.entries(RECORD_TYPE_META) as [RecordType, typeof RECORD_TYPE_META[RecordType]][]).map(
        ([type, meta]) => (
          <button
            key={type}
            type="button"
            onClick={() => onChange(type)}
            className={`flex flex-col items-start gap-1.5 rounded-xl border-2 p-3 text-left transition-all ${
              selected === type
                ? 'border-primary bg-primary/5'
                : 'border-gray-100 bg-white hover:border-gray-200'
            }`}
          >
            <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${
              selected === type ? 'bg-primary/15' : 'bg-gray-100'
            }`}>
              <RecordTypeIcon name={meta.icon} active={selected === type} />
            </div>
            <div>
              <p className={`text-sm font-medium ${selected === type ? 'text-primary' : 'text-gray-700'}`}>
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
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9zm9 3a2 2 0 100 4 2 2 0 000-4z" />
    ),
  }
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke={color}>
      {paths[name]}
    </svg>
  )
}
