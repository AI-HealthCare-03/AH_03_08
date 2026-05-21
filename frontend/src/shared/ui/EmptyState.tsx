import { Button } from '@/components/ui/button'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      {icon && (
        <div
          className="flex h-14 w-14 items-center justify-center rounded-full mb-4"
          style={{ background: '#E1F5EE' }}
        >
          <div style={{ color: '#1D9E75' }}>{icon}</div>
        </div>
      )}
      <p className="text-sm font-medium text-gray-700">{title}</p>
      {description && (
        <p className="text-xs mt-1.5" style={{ color: 'var(--color-text-tertiary)' }}>
          {description}
        </p>
      )}
      {action && (
        <Button
          size="sm"
          className="mt-5 text-white"
          style={{ background: '#1D9E75' }}
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  )
}
