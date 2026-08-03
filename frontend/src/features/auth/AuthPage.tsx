import {
  useState,
  type FormEvent,
} from 'react'
import {
  Link,
  Navigate,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from './auth-context'
import styles from './AuthPage.module.css'


type AuthMode = 'login' | 'register'


export function AuthPage() {
  const navigate = useNavigate()
  const {
    isAuthenticated,
    isLoading,
    login,
    register,
  } = useAuth()

  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = (
    useState(false)
  )

  if (isLoading) {
    return (
      <main className={styles.statusPage}>
        <p role="status">Comprobando sesión...</p>
      </main>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/library" replace />
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setError(null)
    setIsSubmitting(true)

    try {
      if (mode === 'register') {
        await register({
          email,
          password,
          display_name: displayName,
          country_code: 'MX',
        })
      } else {
        await login({
          email,
          password,
        })
      }

      navigate('/library', {
        replace: true,
      })
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

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode)
    setError(null)
  }

  return (
    <main className={styles.page}>
      <section className={styles.intro}>
        <Link className={styles.homeLink} to="/">
          ← Volver a explorar
        </Link>

        <p className={styles.eyebrow}>
          Watch Later Universal
        </p>

        <h1>Guarda tus próximas películas y series.</h1>

        <p className={styles.description}>
          Guarda películas y series para ver después,
          organiza tu progreso y conserva todo en una
          biblioteca personal.
        </p>
      </section>

      <section
        className={styles.card}
        aria-labelledby="auth-title"
      >
        <div className={styles.tabs}>
          <button
            className={styles.tab}
            type="button"
            aria-pressed={mode === 'login'}
            onClick={() => changeMode('login')}
          >
            Iniciar sesión
          </button>

          <button
            className={styles.tab}
            type="button"
            aria-pressed={mode === 'register'}
            onClick={() => changeMode('register')}
          >
            Crear cuenta
          </button>
        </div>

        <h2 id="auth-title">
          {mode === 'login'
            ? 'Bienvenido de vuelta'
            : 'Crea tu biblioteca'}
        </h2>

        <form
          className={styles.form}
          onSubmit={handleSubmit}
        >
          {mode === 'register' && (
            <label className={styles.field}>
              <span>Nombre</span>
              <input
                required
                minLength={2}
                maxLength={100}
                autoComplete="name"
                value={displayName}
                onChange={(event) =>
                  setDisplayName(event.target.value)
                }
              />
            </label>
          )}

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

          <label className={styles.field}>
            <span>Contraseña</span>
            <input
              required
              type="password"
              minLength={
                mode === 'register' ? 12 : 1
              }
              maxLength={128}
              autoComplete={
                mode === 'register'
                  ? 'new-password'
                  : 'current-password'
              }
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />
          </label>

          {mode === 'register' && (
            <p className={styles.hint}>
              Usa al menos 12 caracteres.
            </p>
          )}

          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}

          <button
            className={styles.submit}
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Procesando...'
              : mode === 'login'
                ? 'Entrar'
                : 'Crear cuenta'}
          </button>
        </form>
      </section>
    </main>
  )
}