import {
  createContext,
  useContext,
} from 'react'

import type {
  LoginPayload,
  RegisterPayload,
  User,
} from '../../types/api'


export interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (
    payload: RegisterPayload,
  ) => Promise<void>
  logout: () => Promise<void>
}


export const AuthContext = createContext<
  AuthContextValue | undefined
>(undefined)


export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)

  if (context === undefined) {
    throw new Error(
      'useAuth debe utilizarse dentro de AuthProvider.',
    )
  }

  return context
}