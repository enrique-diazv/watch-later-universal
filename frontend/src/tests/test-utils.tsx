import type { ReactElement } from 'react'
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import {
  render,
  type RenderOptions,
} from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import {
  AuthContext,
  type AuthContextValue,
} from '../features/auth/auth-context'

const defaultAuthValue: AuthContextValue = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  login: () => Promise.resolve(),
  register: () => Promise.resolve(),
  logout: () => Promise.resolve(),
}

interface CustomRenderOptions
  extends Omit<RenderOptions, 'wrapper'> {
  route?: string
  auth?: Partial<AuthContextValue>
}


export function renderWithProviders(
  ui: ReactElement,
  {
    route = '/',
    auth = {},
    ...renderOptions
  }: CustomRenderOptions = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

const authValue: AuthContextValue = {
    ...defaultAuthValue,
    ...auth,
  }
  return render(
    <MemoryRouter initialEntries={[route]}>
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={authValue}>
          {ui}
        </AuthContext.Provider>
      </QueryClientProvider>
    </MemoryRouter>,
    renderOptions,
  )
}