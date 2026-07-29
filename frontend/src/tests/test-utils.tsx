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


interface CustomRenderOptions
  extends Omit<RenderOptions, 'wrapper'> {
  route?: string
}


export function renderWithProviders(
  ui: ReactElement,
  {
    route = '/',
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

  return render(
    <MemoryRouter initialEntries={[route]}>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </MemoryRouter>,
    renderOptions,
  )
}