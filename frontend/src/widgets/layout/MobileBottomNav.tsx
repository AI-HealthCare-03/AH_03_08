import { NavLink } from 'react-router-dom'
import { NAV_ITEMS } from './nav-items'
import { NavIcon } from './NavIcon'

const MOBILE_NAV = ['/home', '/medical-record', '/guide', '/calendar', '/chatbot', '/notification'] as const

export function MobileBottomNav() {
  const items = NAV_ITEMS.filter((i) => MOBILE_NAV.includes(i.path as (typeof MOBILE_NAV)[number]))
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-gray-100">
      <ul className="grid grid-cols-6">
        {items.map((item) => (
          <li key={item.path}>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-1 py-2 text-[11px] ${
                  isActive ? 'text-brand-primary font-semibold' : 'text-gray-500'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <NavIcon name={item.icon} active={isActive} className="h-5 w-5" />
                  <span>{item.label.replace('알림설정', '알림')}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}

