import { screen } from '@testing-library/react'
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { verifyEmail } from '../../services/api'
import { renderWithProviders } from '../../tests/test-utils'
import { VerifyEmailPage } from './VerifyEmailPage'


vi.mock('../../services/api', () => ({
  verifyEmail: vi.fn(),
}))


const mockedVerifyEmail = vi.mocked(verifyEmail)


afterEach(() => {
  vi.resetAllMocks()
})


describe('VerifyEmailPage', () => {
  it('verifies the token from the URL', async () => {
    mockedVerifyEmail.mockResolvedValue({
      message: (
        'Tu correo fue verificado correctamente.'
      ),
    })

    const token = 'a'.repeat(64)

    renderWithProviders(
      <VerifyEmailPage />,
      {
        route: `/verify-email?token=${token}`,
      },
    )

    expect(
      await screen.findByText(
        'Tu correo fue verificado correctamente.',
      ),
    ).toBeInTheDocument()

    expect(mockedVerifyEmail).toHaveBeenCalledWith({
      token,
    })

    expect(
      screen.getByRole('link', {
        name: 'Iniciar sesión',
      }),
    ).toHaveAttribute('href', '/auth')
  })

  it('rejects a URL without a token', async () => {
    renderWithProviders(
      <VerifyEmailPage />,
      {
        route: '/verify-email',
      },
    )

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(
      'El enlace no contiene un token de verificación.',
    )

    expect(mockedVerifyEmail).not.toHaveBeenCalled()
  })
})