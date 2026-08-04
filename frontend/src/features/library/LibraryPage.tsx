import {
  useMemo,
  useState,
} from 'react'
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
import { StarRatingEditor } from './StarRatingEditor'
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

type StatusFilter =
  | 'all'
  | LibraryStatus

type MediaTypeFilter =
  | 'all'
  | 'movie'
  | 'tv'

type LibrarySort =
  | 'recent'
  | 'added'
  | 'title'
  | 'rating'

export function LibraryPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const {
    user,
    isAuthenticated,
    isLoading,
    logout,
  } = useAuth()

  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>('all')
  const [mediaTypeFilter, setMediaTypeFilter] =
    useState<MediaTypeFilter>('all')
  const [favoritesOnly, setFavoritesOnly] =
    useState(false)
  const [sortOrder, setSortOrder] =
    useState<LibrarySort>('recent')

  const libraryQuery = useQuery({
    queryKey: ['library'],
    queryFn: getLibraryItems,
    enabled: isAuthenticated,
  })

  const filteredItems = useMemo(() => {
    const items = libraryQuery.data ?? []
    return items
      .filter((item) => (
        statusFilter === 'all' ||
        item.status === statusFilter
      ))
      .filter((item) => (
        mediaTypeFilter === 'all' ||
        item.media.media_type === mediaTypeFilter
      ))
      .filter((item) => (
        !favoritesOnly ||
        item.is_favorite
      ))
      .sort((leftItem, rightItem) => {
        if (sortOrder === 'title') {
          return leftItem.media.title.localeCompare(
            rightItem.media.title,
            'es',
            {
              sensitivity: 'base',
            },
          )
        }

        if (sortOrder === 'rating') {
          return (
            (rightItem.user_rating ?? -1) -
            (leftItem.user_rating ?? -1)
          )
        }

        const leftDate = Date.parse(
          sortOrder === 'added'
            ? leftItem.added_at
            : leftItem.updated_at,
        )
        const rightDate = Date.parse(
          sortOrder === 'added'
            ? rightItem.added_at
            : rightItem.updated_at,
        )

        return rightDate - leftDate
      })
  }, [
    favoritesOnly,
    libraryQuery.data,
    mediaTypeFilter,
    sortOrder,
    statusFilter,
  ])
  const hasActiveFilters = (
    statusFilter !== 'all' ||
    mediaTypeFilter !== 'all' ||
    favoritesOnly ||
    sortOrder !== 'recent'
  )
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
  function clearFilters() {
    setStatusFilter('all')
    setMediaTypeFilter('all')
    setFavoritesOnly(false)
    setSortOrder('recent')
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

      {libraryQuery.data &&
        libraryQuery.data.length > 0 && (
          <section
            className={styles.filtersPanel}
            aria-label="Filtros de biblioteca"
          >
            <div className={styles.filtersGrid}>
              <label className={styles.filterControl}>
                <span>Estado</span>
                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(
                      event.target.value as StatusFilter,
                    )
                  }
                >
                  <option value="all">
                    Todos
                  </option>
                  {Object.entries(statusLabels).map(
                    ([value, label]) => (
                      <option
                        value={value}
                        key={value}
                      >
                        {label}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label className={styles.filterControl}>
                <span>Tipo</span>
                <select
                  value={mediaTypeFilter}
                  onChange={(event) =>
                    setMediaTypeFilter(
                      event.target.value as MediaTypeFilter,
                    )
                  }
                >
                  <option value="all">
                    Películas y series
                  </option>
                  <option value="movie">
                    Películas
                  </option>
                  <option value="tv">
                    Series
                  </option>
                </select>
              </label>

              <label className={styles.filterControl}>
                <span>Ordenar</span>
                <select
                  value={sortOrder}
                  onChange={(event) =>
                    setSortOrder(
                      event.target.value as LibrarySort,
                    )
                  }
                >
                  <option value="recent">
                    Actualizados recientemente
                  </option>
                  <option value="added">
                    Agregados recientemente
                  </option>
                  <option value="title">
                    Título
                  </option>
                  <option value="rating">
                    Mi calificación
                  </option>
                </select>
              </label>

              <label className={styles.favoriteFilter}>
                <input
                  type="checkbox"
                  checked={favoritesOnly}
                  onChange={(event) =>
                    setFavoritesOnly(
                      event.target.checked,
                    )
                  }
                />
                <span>Solo favoritos</span>
              </label>

              <button
                className={styles.clearFiltersButton}
                type="button"
                disabled={!hasActiveFilters}
                onClick={clearFilters}
              >
                Limpiar filtros
              </button>
            </div>

            <p
              className={styles.resultsCount}
              aria-live="polite"
            >
              {filteredItems.length}
              {filteredItems.length === 1
                ? ' elemento'
                : ' elementos'}
            </p>
          </section>
        )}

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
        libraryQuery.data.length > 0 &&
        filteredItems.length === 0 && (
          <section className={styles.noResults}>
            <h2>No hay coincidencias.</h2>
            <p>
              Prueba otra combinación de filtros.
            </p>
            <button
              type="button"
              onClick={clearFilters}
            >
              Limpiar filtros
            </button>
          </section>
        )}
      {filteredItems.length > 0 && (
        <section
          className={styles.grid}
          aria-label="Contenido guardado"
        >
          {filteredItems.map((item) => {
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
                  <StarRatingEditor
                    value={item.user_rating}
                    disabled={isUpdating}
                    onSave={async (userRating) => {
                      await updateMutation.mutateAsync({
                        itemId: item.id,
                        payload: {
                          user_rating: userRating,
                        },
                      })
                    }}
                  />

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