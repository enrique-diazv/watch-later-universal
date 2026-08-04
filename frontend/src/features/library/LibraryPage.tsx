import type { FormEvent } from 'react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  Link,
  Navigate,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from '../auth/auth-context'
import {
  deleteLibraryItem,
  getLibraryItems,
  updateLibraryItem,
} from '../../services/api'
import type {
  LibraryStatus,
  UpdateLibraryItemPayload,
} from '../../types/api'
import styles from './LibraryPage.module.css'


const POSTER_BASE_URL =
  'https://image.tmdb.org/t/p/w500'

const statusLabels: Record<LibraryStatus, string> = {
  plan_to_watch: 'Ver después',
  watching: 'Viendo',
  completed: 'Completado',
  paused: 'En pausa',
  dropped: 'Abandonado',
}


interface UpdateVariables {
  itemId: string
  payload: UpdateLibraryItemPayload
}


export function LibraryPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const {
    user,
    isAuthenticated,
    isLoading,
    logout,
  } = useAuth()

  const libraryQuery = useQuery({
    queryKey: ['library'],
    queryFn: getLibraryItems,
    enabled: isAuthenticated,
  })

  const updateMutation = useMutation({
    mutationFn: ({
      itemId,
      payload,
    }: UpdateVariables) =>
      updateLibraryItem(itemId, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ['library'],
      }),
  })

  const deleteMutation = useMutation({
  mutationFn: (itemId: string) =>
    deleteLibraryItem(itemId),
  onSuccess: () =>
    queryClient.invalidateQueries({
      queryKey: ['library'],
    }),
})

  if (isLoading) {
    return (
      <main className={styles.statusPage}>
        <p role="status">Cargando tu sesión...</p>
      </main>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }

  async function handleLogout() {
    try {
      await logout()
    } finally {
      navigate('/auth', {
        replace: true,
      })
    }
  }
  function handleDetailsSubmit(
    event: FormEvent<HTMLFormElement>,
    itemId: string,
  ) {
    event.preventDefault()

    const formData = new FormData(
      event.currentTarget,
    )
    const ratingValue = String(
      formData.get('user_rating') ?? '',
    ).trim()
    const notesValue = String(
      formData.get('notes') ?? '',
    ).trim()

    updateMutation.mutate({
      itemId,
      payload: {
        user_rating:
          ratingValue === ''
            ? null
            : Number(ratingValue),
        notes:
          notesValue === ''
            ? null
            : notesValue,
      },
    })
  }
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>
            Watch Later Universal
          </p>
          <h1>Mi biblioteca</h1>
          <p className={styles.welcome}>
            {user
              ? `Hola, ${user.display_name}.`
              : 'Tu lista personal.'}
          </p>
        </div>

        <nav className={styles.navigation}>
          <Link className={styles.exploreLink} to="/">
            Explorar
          </Link>
          <button
            className={styles.logoutButton}
            type="button"
            onClick={() => void handleLogout()}
          >
            Cerrar sesión
          </button>
        </nav>
      </header>

      {libraryQuery.isPending && (
        <p className={styles.status} role="status">
          Cargando biblioteca...
        </p>
      )}

      {libraryQuery.isError && (
        <p className={styles.error} role="alert">
          {libraryQuery.error.message}
        </p>
      )}

      {libraryQuery.data?.length === 0 && (
        <section className={styles.empty}>
          <h2>Tu lista está esperando.</h2>
          <p>
            Explora películas y series, abre sus detalles
            y selecciona “Guardar para después”.
          </p>
          <Link className={styles.primaryLink} to="/">
            Buscar contenido
          </Link>
        </section>
      )}

      {libraryQuery.data &&
        libraryQuery.data.length > 0 && (
          <section
            className={styles.grid}
            aria-label="Contenido guardado"
          >
            {libraryQuery.data.map((item) => {
              const isUpdating = (
                updateMutation.isPending &&
                updateMutation.variables?.itemId
                  === item.id
              )
              const isDeleting = (
                deleteMutation.isPending &&
                deleteMutation.variables === item.id
              )

              return (
                <article
                  className={styles.card}
                  key={item.id}
                >
                  {item.media.poster_path ? (
                    <img
                      className={styles.poster}
                      src={
                        POSTER_BASE_URL +
                        item.media.poster_path
                      }
                      alt={`Póster de ${item.media.title}`}
                    />
                  ) : (
                    <div
                      className={styles.posterPlaceholder}
                    >
                      Sin póster
                    </div>
                  )}

                  <div className={styles.cardContent}>
                    <p className={styles.mediaType}>
                      {item.media.media_type === 'movie'
                        ? 'Película'
                        : 'Serie'}
                    </p>

                    <h2>
                      <Link
                        className={styles.titleLink}
                        to={
                          `/media/` +
                          `${item.media.media_type}/` +
                          item.media.tmdb_id
                        }
                      >
                        {item.media.title}
                      </Link>
                    </h2>

                    <p className={styles.meta}>
                      {item.media.release_date
                        ?.slice(0, 4) ??
                        'Año desconocido'}
                      {' · '}
                      {item.media.tmdb_rating.toFixed(1)}
                      /10
                    </p>

                    <label className={styles.statusControl}>
                      <span>Estado</span>
                      <select
                        value={item.status}
                        disabled={isUpdating}
                        onChange={(event) =>
                          updateMutation.mutate({
                            itemId: item.id,
                            payload: {
                              status: (
                                event.target.value as LibraryStatus
                              ),
                            },
                          })
                        }
                      >
                        {Object.entries(
                          statusLabels,
                        ).map(([value, label]) => (
                          <option
                            value={value}
                            key={value}
                          >
                            {label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <form
                      className={styles.detailsForm}
                      onSubmit={(event) =>
                        handleDetailsSubmit(
                          event,
                          item.id,
                        )
                      }
                    >
                      <label className={styles.ratingControl}>
                        <span>Tu calificación</span>
                        <input
                          name="user_rating"
                          type="number"
                          min="0"
                          max="10"
                          step="0.5"
                          defaultValue={
                            item.user_rating ?? ''
                          }
                          disabled={isUpdating}
                          placeholder="0–10"
                        />
                      </label>

                      <label className={styles.notesControl}>
                        <span>Notas personales</span>
                        <textarea
                          name="notes"
                          rows={3}
                          maxLength={2000}
                          defaultValue={item.notes ?? ''}
                          disabled={isUpdating}
                          placeholder="¿Qué te interesa recordar?"
                        />
                      </label>

                      <button
                        type="submit"
                        disabled={isUpdating}
                      >
                        {isUpdating
                          ? 'Guardando...'
                          : 'Guardar detalles'}
                      </button>
                    </form>



                    <div className={styles.actions}>
                      <button
                        type="button"
                        disabled={isUpdating}
                        onClick={() =>
                          updateMutation.mutate({
                            itemId: item.id,
                            payload: {
                              is_favorite:
                                !item.is_favorite,
                            },
                          })
                        }
                      >
                        {item.is_favorite
                          ? '★ Favorito'
                          : '☆ Favorito'}
                      </button>

                      <button
                        className={styles.removeButton}
                        type="button"
                        disabled={isDeleting}
                        onClick={() =>
                          deleteMutation.mutate(item.id)
                        }
                      >
                        {isDeleting
                          ? 'Quitando...'
                          : 'Quitar'}
                      </button>
                    </div>
                  </div>
                </article>
              )
            })}
          </section>
        )}

      {(updateMutation.isError ||
        deleteMutation.isError) && (
        <p className={styles.error} role="alert">
          No fue posible actualizar tu biblioteca.
        </p>
      )}
    </main>
  )
}