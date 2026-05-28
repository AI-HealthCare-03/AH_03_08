export interface NavItem {
  path: string
  label: string
  icon: string
}

export const NAV_ITEMS: NavItem[] = [
  { path: '/home', label: '홈', icon: 'home' },
  { path: '/medical-record', label: '의료기록', icon: 'file-medical' },
  { path: '/guide', label: '가이드', icon: 'book-open' },
  { path: '/challenge', label: '챌린지', icon: 'flag' },
  { path: '/nutrition', label: '영양 상담', icon: 'utensils' },
  { path: '/chatbot', label: '챗봇', icon: 'message-circle' },
  { path: '/calendar', label: '캘린더', icon: 'calendar' },
  { path: '/notification', label: '알림설정', icon: 'bell' },
  { path: '/my-page', label: '마이페이지', icon: 'user' },
]
