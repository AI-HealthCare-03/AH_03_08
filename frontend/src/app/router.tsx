import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/app/providers/auth-store'
import { AppShell } from '@/widgets/layout/AppShell'
import { LandingPage } from '@/pages/landing'
import { LoginPage } from '@/pages/auth'
import { RegisterPage } from '@/pages/auth/register'
import { GoogleCallbackPage } from '@/pages/auth/google-callback'
import { KakaoCallbackPage } from '@/pages/auth/kakao-callback'
import { HomePage } from '@/pages/home'
import { MedicalRecordPage } from '@/pages/medical-record'
import { GuidePage } from '@/pages/guide'
import { ChatbotPage } from '@/pages/chatbot'
import { CalendarPage } from '@/pages/calendar'
import { NotificationPage } from '@/pages/notification'
import { MyPage } from '@/pages/my-page'

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())
  return isAuthenticated ? <Outlet /> : <Navigate to="/auth/login" replace />
}

function RootRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())
  return isAuthenticated ? <Navigate to="/home" replace /> : <Navigate to="/auth/login" replace />
}

export const router = createBrowserRouter([
  { path: '/', element: <RootRoute /> },
  { path: '/auth/login', element: <LoginPage /> },
  { path: '/auth/register', element: <RegisterPage /> },
  { path: '/auth/google/callback', element: <GoogleCallbackPage /> },
  { path: '/auth/kakao/callback', element: <KakaoCallbackPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: '/home', element: <HomePage /> },
          { path: '/medical-record', element: <MedicalRecordPage /> },
          { path: '/guide', element: <GuidePage /> },
          { path: '/chatbot', element: <ChatbotPage /> },
          { path: '/chatbot/:sessionId', element: <ChatbotPage /> },
          { path: '/calendar', element: <CalendarPage /> },
          { path: '/notification', element: <NotificationPage /> },
          { path: '/my-page', element: <MyPage /> },
        ],
      },
    ],
  },
])