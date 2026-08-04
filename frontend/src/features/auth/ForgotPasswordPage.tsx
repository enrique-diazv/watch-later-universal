import {
  useState,
  type FormEvent,
} from 'react'
import { Link } from 'react-router-dom'

import { requestPasswordReset } from '../../services/api'
import styles from './AuthPage.module.css'


export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(
    null,
  )
  const [notice, setNotice] = useState<string | null>(
    null,
  )
  const [isSubmitting, setIsSubmitting] = (
    useState(false)
  )

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    setIsSubmitting(true)

    try {
      const response = await requestPasswordReset({
        email: email.trim().toLowerCase(),
      })

      setNotice(response.message)
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : 'No fue posible completar la solicitud.',
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

        <h1>Recupera el acceso a tu biblioteca.</h1>

        <p className={styles.description}>
          Te enviaremos un enlace seguro para crear una
          contraseña nueva.
        </p>
      </section>

      <section
        className={styles.card}
        aria-labelledby="forgot-password-title"
      >
        <h2 id="forgot-password-title">
          Olvidé mi contraseña
        </h2>

        <form
          className={styles.form}
          onSubmit={handleSubmit}
        >
          <label className={styles.field}>
            <span>Correo electrónico</span>
            <input
              required
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
            />
          </label>

          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}

          {notice && (
            <p className={styles.notice} role="status">
              {notice}
            </p>
          )}

          <button
            className={styles.submit}
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Enviando...'
              : 'Enviar enlace'}
          </button>
        </form>
      </section>
    </main>
  )
}