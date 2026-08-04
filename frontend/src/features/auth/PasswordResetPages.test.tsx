import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import {
  requestPasswordReset,
  resetPassword,
} from '../../services/api'
import { renderWithProviders } from '../../tests/test-utils'
import { ForgotPasswordPage } from './ForgotPasswordPage'
import { ResetPasswordPage } from './ResetPasswordPage'


vi.mock('../../services/api', () => ({
  requestPasswordReset: vi.fn(),
  resetPassword: vi.fn(),
}))


const mockedRequestPasswordReset = vi.mocked(
  requestPasswordReset,
)
const mockedResetPassword = vi.mocked(
  resetPassword,
)


afterEach(() => {
  vi.resetAllMocks()
})


describe('Password reset pages', () => {
  it('requests a password reset email', async () => {
    mockedRequestPasswordReset.mockResolvedValue({
      message: (
        'Si existe una cuenta verificada con ese correo, '
        + 'enviaremos instrucciones para restablecer '
        + 'la contraseña.'
      ),
    })

    const user = userEvent.setup()

    renderWithProviders(<ForgotPasswordPage />)

    await user.type(
      screen.getByLabelText(/correo electrónico/i),
      'LEARNER@example.com',
    )

    await user.click(
      screen.getByRole('button', {
        name: 'Enviar enlace',
      }),
    )

    expect(
      await screen.findByRole('status'),
    ).toHaveTextContent(
      'Si existe una cuenta verificada',
    )

    expect(
      mockedRequestPasswordReset,
    ).toHaveBeenCalledWith({
      email: 'learner@example.com',
    })
  })

  it('sets a new password using the URL token', async () => {
    mockedResetPassword.mockResolvedValue({
      message: (
        'Tu contraseña fue actualizada correctamente.'
      ),
    })

    const user = userEvent.setup()
    const token = 'a'.repeat(64)

    renderWithProviders(
      <ResetPasswordPage />,
      {
        route: `/reset-password?token=${token}`,
      },
    )

    await user.type(
      screen.getByLabelText('Contraseña nueva'),
      'new-safe-learning-password',
    )
    await user.type(
      screen.getByLabelText('Confirmar contraseña'),
      'new-safe-learning-password',
    )

    await user.click(
      screen.getByRole('button', {
        name: 'Guardar contraseña',
      }),
    )

    expect(
      await screen.findByRole('status'),
    ).toHaveTextContent(
      'Tu contraseña fue actualizada correctamente.',
    )

    expect(mockedResetPassword).toHaveBeenCalledWith({
      token,
      new_password: 'new-safe-learning-password',
    })

    expect(
      screen.getByRole('link', {
        name: 'Ir a iniciar sesión',
      }),
    ).toHaveAttribute('href', '/auth')
  })

  it('rejects passwords that do not match', async () => {
    const user = userEvent.setup()
    const token = 'a'.repeat(64)

    renderWithProviders(
      <ResetPasswordPage />,
      {
        route: `/reset-password?token=${token}`,
      },
    )

    await user.type(
      screen.getByLabelText('Contraseña nueva'),
      'new-safe-learning-password',
    )
    await user.type(
      screen.getByLabelText('Confirmar contraseña'),
      'different-safe-password',
    )

    await user.click(
      screen.getByRole('button', {
        name: 'Guardar contraseña',
      }),
    )

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(
      'Las contraseñas no coinciden.',
    )

    expect(mockedResetPassword).not.toHaveBeenCalled()
  })
})