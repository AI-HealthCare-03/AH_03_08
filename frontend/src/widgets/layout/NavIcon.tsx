interface IconProps {
  name: string
  active?: boolean
  className?: string
}

const icons: Record<string, React.ReactNode> = {
  home: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H5a1 1 0 01-1-1V9.5z" />
  ),
  'file-medical': (
    <>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9 12h6m-3-3v6M7 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2h-2" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M9 3h6v2H9V3z" />
    </>
  ),
  'book-open': (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  ),
  'message-circle': (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  ),
  calendar: (
    <>
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M16 2v4M8 2v4M3 10h18" />
    </>
  ),
  bell: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  ),
  user: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  ),
  flag: (
    <>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M6 3v18" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M6 4h10l-1 3 1 3H6" />
    </>
  ),
  utensils: (
    <>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M6 2v10M9 2v10M6 7h3" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M14 2v8a3 3 0 006 0V2" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
        d="M17 10v12" />
    </>
  ),
}

// active 시 연초록색 (#22ad28), 비활성은 currentColor(부모 text 색 상속)
export function NavIcon({ name, active = false, className = 'h-5 w-5' }: IconProps) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke={active ? '#1D9E75' : 'currentColor'}
    >
      {icons[name] ?? null}
    </svg>
  )
}
