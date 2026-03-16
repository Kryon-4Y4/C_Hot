import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
}

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: User | null
  setAuth: (token: string, refreshToken: string, user: User) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      
      setAuth: (token, refreshToken, user) => {
        set({ token, refreshToken, user })
      },
      
      clearAuth: () => {
        set({ token: null, refreshToken: null, user: null })
      },
      
      isAuthenticated: () => {
        return !!get().token
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
