import { useState } from 'react'
import { useNavigate, NavLink } from 'react-router-dom'
import { NAV_ITEMS } from './nav-items'
import { NavIcon } from './NavIcon'
import { useCurrentUser } from '@/entities/user/api'
import { useAuthStore } from '@/app/providers/auth-store'
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog'

export function Sidebar() {
  const { data: user } = useCurrentUser()
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const [confirmOpen, setConfirmOpen] = useState(false)

  function handleLogout() {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <aside className="hidden md:flex flex-col w-60 min-h-screen border-r border-gray-100 bg-[#F5F5F4] px-4 py-6 shrink-0">
      <div className="mb-8 px-2">
        <span className="text-lg font-bold" style={{ color: '#1D9E75' }}>메디로그</span>
        <p className="text-xs text-gray-500 mt-0.5">건강 기록 기반 관리가이드</p>
      </div>

      <nav className="flex flex-col gap-1 flex-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
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

      <div className="mt-auto pt-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          {/* 유저 정보 → 마이페이지 이동 */}
          <button
            onClick={() => navigate('/my-page')}
            className="flex items-center gap-3 flex-1 min-w-0 px-2 py-2 rounded-xl hover:bg-gray-100 transition-colors text-left"
          >
            <div
              className="h-9 w-9 shrink-0 rounded-full flex items-center justify-center text-sm font-semibold"
              style={{ background: '#E1F5EE', color: '#0F6E56' }}
            >
              {user ? user.name.charAt(0) : '?'}
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

          {/* 로그아웃 버튼 */}
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

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="로그아웃 하시겠습니까?"
        description="로그아웃하면 다시 로그인해야 합니다."
        confirmLabel="로그아웃"
        variant="danger"
        onConfirm={handleLogout}
      />
    </aside>
  )
}
