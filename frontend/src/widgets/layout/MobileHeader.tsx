import { useState, useEffect } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { NAV_ITEMS } from './nav-items'
import { NavIcon } from './NavIcon'
import { useAuthStore } from '@/app/providers/auth-store'
import { useCurrentUser } from '@/entities/user/api'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'

export function MobileHeader() {
  const [open, setOpen] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const { data: user } = useCurrentUser()

  useEffect(() => { setOpen(false) }, [location.pathname])

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  function handleLogout() {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <>
      {/* 모바일 상단 헤더 */}
      <header className="md:hidden fixed top-0 inset-x-0 z-40 flex items-center justify-between px-4 h-14 bg-white border-b border-gray-100">
        <span className="text-base font-bold" style={{ color: '#1D9E75' }}>메디로그</span>
        <button
          onClick={() => setOpen(true)}
          aria-label="메뉴 열기"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <HamburgerIcon />
        </button>
      </header>

      {/* 백드롭 */}
      {open && (
        <div
          className="md:hidden fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        />
      )}

      {/* 드로어 */}
      <div
        className={`md:hidden fixed top-0 right-0 z-50 h-full w-64 bg-[#F5F5F4] shadow-xl flex flex-col transition-transform duration-300 ease-in-out
          ${open ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="flex items-center justify-between px-5 h-14 border-b border-gray-100">
          <span className="text-base font-bold" style={{ color: '#1D9E75' }}>메디로그</span>
          <button
            onClick={() => setOpen(false)}
            aria-label="메뉴 닫기"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 transition-colors"
          >
            <CloseIcon />
          </button>
        </div>

        <nav className="flex flex-col gap-1 p-3 flex-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-3 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary font-bold'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <NavIcon name={item.icon} active={isActive} />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* 하단 유저 정보 + 로그아웃 */}
        <div className="p-3 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/my-page')}
              className="flex items-center gap-3 flex-1 min-w-0 px-2 py-2 rounded-xl hover:bg-gray-100 transition-colors text-left"
            >
              <div
                className="h-9 w-9 shrink-0 rounded-full flex items-center justify-center text-sm font-semibold"
                style={{ background: '#E1F5EE', color: '#0F6E56' }}
              >
                {user ? (user.name?.charAt(0) ?? '?') : '?'}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {user ? user.name : '사용자'}
                </p>
                <p className="text-xs truncate" style={{ color: 'var(--color-text-tertiary)' }}>
                  {user ? user.email : '로그인이 필요합니다'}
                </p>
              </div>
            </button>

            <button
              onClick={() => setConfirmOpen(true)}
              title="로그아웃"
              className="shrink-0 flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-red-500 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="로그아웃 하시겠습니까?"
        description="로그아웃하면 다시 로그인해야 합니다."
        confirmLabel="로그아웃"
        variant="danger"
        onConfirm={handleLogout}
      />
    </>
  )
}

function HamburgerIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
