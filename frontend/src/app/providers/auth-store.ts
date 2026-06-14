import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/entities/user/model'

interface AuthState {
  user: User | null
  accessToken: string | null
  isAdmin: boolean
  setTokens: (accessToken: string, isAdmin?: boolean) => void
  setUser: (user: User) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAdmin: false,
      setTokens: (accessToken, isAdmin = false) => {
        localStorage.setItem('access_token', accessToken)
        set({ accessToken, isAdmin })
      },
      setUser: (user) => set({ user }),
      logout: () => {
        localStorage.removeItem('access_token')
        set({ user: null, accessToken: null, isAdmin: false })
      },
      isAuthenticated: () => {
        const token = get().accessToken
        if (!token) return false
        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          return payload.exp * 1000 > Date.now()
        } catch {
          return false
        }
      },
    }),
    { name: 'auth-storage', partialize: (s) => ({ user: s.user, accessToken: s.accessToken, isAdmin: s.isAdmin }) },
  ),
)