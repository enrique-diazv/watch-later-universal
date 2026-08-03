import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { resendVerificationEmail } from '../../services/api'
import { renderWithProviders } from '../../tests/test-utils'
import { AuthPage } from './AuthPage'


vi.mock(
  '../../services/api',
  async (importOriginal) => {
    const actual = await importOriginal<
      typeof import('../../services/api')
    >()

    return {
      ...actual,
      resendVerificationEmail: vi.fn(),
    }
  },
)


const mockedResend = vi.mocked(
  resendVerificationEmail,
)


afterEach(() => {
  vi.resetAllMocks()
})


describe('AuthPage', () => {
  it('waits for email verification after registration', async () => {
    const register = vi.fn().mockResolvedValue(undefined)
    const login = vi.fn().mockResolvedValue(undefined)

    mockedResend.mockResolvedValue({
      message: (
        'Si existe una cuenta pendiente con ese correo, '
        + 'enviaremos un nuevo enlace de verificación.'
      ),
    })

    const user = userEvent.setup()

    renderWithProviders(
      <AuthPage />,
      {
        route: '/auth',
        auth: {
          register,
          login,
        },
      },
    )

    await user.click(
        screen.getByRole('button', {
            name: 'Crear cuenta',
        }),
    )

    await user.type(
      screen.getByLabelText('Nombre'),
      'Learner',
    )
    await user.type(
      screen.getByLabelText(/correo/i),
      'LEARNER@example.com',
    )
    await user.type(
      screen.getByLabelText(/contrase/i),
      'safe-learning-password',
    )

    const createAccountButtons = screen.getAllByRole(
        'button',
        {
            name: 'Crear cuenta',
        },
    )

    await user.click(createAccountButtons[1])

    expect(register).toHaveBeenCalledWith({
      email: 'learner@example.com',
      password: 'safe-learning-password',
      display_name: 'Learner',
      country_code: 'MX',
    })
    expect(login).not.toHaveBeenCalled()

    expect(
      await screen.findByText(
        /cuenta creada.*revisa tu correo/i,
      ),
    ).toBeInTheDocument()

    const resendButton = screen.getByRole(
      'button',
      {
        name: 'Reenviar correo de confirmación',
      },
    )

    await user.click(resendButton)

    expect(mockedResend).toHaveBeenCalledWith({
      email: 'learner@example.com',
    })
  })
})