import {
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  AuthContext,
  type AuthContextValue,
} from './auth-context'

import {
  getCurrentUser,
  loginUser,
  logoutSession,
  refreshSession,
  registerUser,
} from '../../services/api'
import type {
  LoginPayload,
  RegisterPayload,
  User,
} from '../../types/api'

let restoreRequest: Promise<User | null> | null = null


function restoreCurrentSession(
): Promise<User | null> {
  if (restoreRequest === null) {
    restoreRequest = (async () => {
      try {
        await refreshSession()

        return await getCurrentUser()
      } catch {
        return null
      }
    })()

    const currentRequest = restoreRequest

    void currentRequest.finally(() => {
      if (restoreRequest === currentRequest) {
        restoreRequest = null
      }
    })
  }

  return restoreRequest
}


interface AuthProviderProps {
  children: ReactNode
}


export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isActive = true

    void restoreCurrentSession().then(
      (restoredUser) => {
        if (isActive) {
          setUser(restoredUser)
          setIsLoading(false)
        }
      },
    )

    return () => {
      isActive = false
    }
  }, [])

  async function login(
    payload: LoginPayload,
  ): Promise<void> {
    await loginUser(payload)

    const currentUser = await getCurrentUser()

    setUser(currentUser)
  }

  async function register(
    payload: RegisterPayload,
  ): Promise<void> {
    await registerUser(payload)

    await login({
      email: payload.email,
      password: payload.password,
    })
  }

  async function logout(): Promise<void> {
    try {
      await logoutSession()
    } finally {
      setUser(null)
    }
  }

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    register,
    logout,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}


