import {
  useState,
  type FormEvent,
} from 'react'
import {
  Link,
  useSearchParams,
} from 'react-router-dom'

import { resetPassword } from '../../services/api'
import styles from './AuthPage.module.css'


export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = (
    useState('')
  )
  const [error, setError] = useState<string | null>(
    token
      ? null
      : 'El enlace de recuperación está incompleto.',
  )
  const [notice, setNotice] = useState<string | null>(
    null,
  )
  const [isSubmitting, setIsSubmitting] = (
    useState(false)
  )
  const [isComplete, setIsComplete] = useState(false)

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError(null)
    setNotice(null)

    if (!token) {
      setError(
        'El enlace de recuperación está incompleto.',
      )
      return
    }

    if (password !== passwordConfirmation) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setIsSubmitting(true)

    try {
      const response = await resetPassword({
        token,
        new_password: password,
      })

      setNotice(response.message)
      setPassword('')
      setPasswordConfirmation('')
      setIsComplete(true)
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : 'No fue posible cambiar la contraseña.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.intro}>
        <Link className={styles.homeLink} to="/auth">
          ← Volver a iniciar sesión
        </Link>

        <p className={styles.eyebrow}>
          Watch Later Universal
        </p>

        <h1>Crea una contraseña nueva.</h1>

        <p className={styles.description}>
          Al completar el cambio, tus sesiones anteriores
          dejarán de ser válidas.
        </p>
      </section>

      <section
        className={styles.card}
        aria-labelledby="reset-password-title"
      >
        <h2 id="reset-password-title">
          Restablecer contraseña
        </h2>

        {isComplete ? (
          <>
            <p className={styles.notice} role="status">
              {notice}
            </p>

            <Link
              className={styles.forgotPasswordLink}
              to="/auth"
            >
              Ir a iniciar sesión
            </Link>
          </>
        ) : (
          <form
            className={styles.form}
            onSubmit={handleSubmit}
          >
            <label className={styles.field}>
              <span>Contraseña nueva</span>
              <input
                required
                type="password"
                minLength={12}
                maxLength={128}
                autoComplete="new-password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
              />
            </label>

            <label className={styles.field}>
              <span>Confirmar contraseña</span>
              <input
                required
                type="password"
                minLength={12}
                maxLength={128}
                autoComplete="new-password"
                value={passwordConfirmation}
                onChange={(event) =>
                  setPasswordConfirmation(
                    event.target.value,
                  )
                }
              />
            </label>

            <p className={styles.hint}>
              Usa al menos 12 caracteres.
            </p>

            {error && (
              <p className={styles.error} role="alert">
                {error}
              </p>
            )}

            <button
              className={styles.submit}
              type="submit"
              disabled={
                isSubmitting ||
                token === null
              }
            >
              {isSubmitting
                ? 'Guardando...'
                : 'Guardar contraseña'}
            </button>
          </form>
        )}
      </section>
    </main>
  )
}