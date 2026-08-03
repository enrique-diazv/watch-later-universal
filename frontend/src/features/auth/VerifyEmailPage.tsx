import {
  useEffect,
  useState,
} from 'react'
import {
  Link,
  useSearchParams,
} from 'react-router-dom'

import { verifyEmail } from '../../services/api'
import type { MessageResponse } from '../../types/api'
import styles from './VerifyEmailPage.module.css'


type VerificationState =
  | 'loading'
  | 'success'
  | 'error'


let activeVerification:
  | {
      token: string
      request: Promise<MessageResponse>
    }
  | null = null


function verifyEmailOnce(
  token: string,
): Promise<MessageResponse> {
  if (
    activeVerification !== null
    && activeVerification.token === token
  ) {
    return activeVerification.request
  }

  const request = verifyEmail({
    token,
  })

  activeVerification = {
    token,
    request,
  }

  const clearRequest = () => {
    if (activeVerification?.request === request) {
      activeVerification = null
    }
  }

  void request.then(
    clearRequest,
    clearRequest,
  )

  return request
}


export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [verificationState, setVerificationState] = (
    useState<VerificationState>('loading')
  )
  const [message, setMessage] = useState(
    'Confirmando tu correo...',
  )

  useEffect(() => {
    if (token === null || token.length === 0) {
      setVerificationState('error')
      setMessage(
        'El enlace no contiene un token de verificación.',
      )
      return
    }

    let isActive = true

    setVerificationState('loading')
    setMessage('Confirmando tu correo...')

    void verifyEmailOnce(token).then(
      (response) => {
        if (isActive) {
          setVerificationState('success')
          setMessage(response.message)
        }
      },
      (error: unknown) => {
        if (isActive) {
          setVerificationState('error')
          setMessage(
            error instanceof Error
              ? error.message
              : 'No fue posible confirmar el correo.',
          )
        }
      },
    )

    return () => {
      isActive = false
    }
  }, [token])

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <p className={styles.eyebrow}>
          Watch Later Universal
        </p>

        <h1>Confirmación de correo</h1>

        <p
          className={
            verificationState === 'error'
              ? styles.error
              : styles.message
          }
          role={
            verificationState === 'error'
              ? 'alert'
              : 'status'
          }
        >
          {message}
        </p>

        {verificationState === 'success' && (
          <Link className={styles.primary} to="/auth">
            Iniciar sesión
          </Link>
        )}

        {verificationState === 'error' && (
          <Link className={styles.secondary} to="/auth">
            Volver al acceso
          </Link>
        )}
      </section>
    </main>
  )
}