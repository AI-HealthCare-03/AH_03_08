interface PollingStatusProps {
  message?: string
}

export function PollingStatus({ message = 'AI가 분석 중입니다...' }: PollingStatusProps) {
  return (
    <div className="flex items-center gap-3 rounded-xl px-4 py-3" style={{ background: '#E1F5EE' }}>
      <div className="flex gap-1 shrink-0">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="inline-block h-1.5 w-1.5 rounded-full animate-bounce"
            style={{ background: '#1D9E75', animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
      <p className="text-xs font-medium" style={{ color: '#0F6E56' }}>
        {message}
      </p>
    </div>
  )
}
