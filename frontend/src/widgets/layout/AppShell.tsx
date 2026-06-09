import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { MobileHeader } from './MobileHeader'
import { MobileBottomNav } from './MobileBottomNav'

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0">
        <MobileHeader />
        <main className="flex-1 overflow-y-auto pt-4 px-6 pb-20 md:pt-8 md:px-10 md:pb-10">
          <Outlet />
        </main>
        <MobileBottomNav />
      </div>
    </div>
  )
}
