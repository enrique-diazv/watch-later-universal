import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/auth-context'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { getLibraryItems, searchMedia } from '../../services/api'
import styles from './SearchPage.module.css'


export function SearchPage() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const {
    isAuthenticated,
    isLoading: isAuthLoading,
  } = useAuth()

  const libraryQuery = useQuery({
    queryKey: ['library'],
    queryFn: getLibraryItems,
    enabled: (
      isAuthenticated &&
      !isAuthLoading
    ),
  })

  const savedMediaKeys = new Set(
    (libraryQuery.data ?? []).map(
      (item) =>
        `${item.media.media_type}-${item.media.tmdb_id}`,
    ),
  )
  const normalizedQuery = query.trim()
  const debouncedQuery = useDebouncedValue(
    normalizedQuery,
    400,
  )
  const canSearch = debouncedQuery.length >= 2

  const searchQuery = useQuery({
    queryKey: ['search', debouncedQuery, page],
    queryFn: () => searchMedia(
      debouncedQuery,
      page,
    ),
    enabled: canSearch,
  })

  const results = searchQuery.data?.results ?? []
  const currentPage = searchQuery.data?.page ?? page
  const totalPages = searchQuery.data?.total_pages ?? 0
  return (
    <main className={styles.page}>
      <header className={styles.hero}>
        <div className={styles.heroCopy}>
          <h1>Watch Later Universal</h1>
          <p>
            Busca películas y series en un solo lugar.
          </p>
        </div>

        <Link
          className={styles.accountLink}
          to={
            isAuthenticated
              ? '/library'
              : '/auth'
          }
        >
          {isAuthLoading
            ? 'Comprobando sesión...'
            : isAuthenticated
              ? 'Mi biblioteca'
              : 'Iniciar sesión'}
        </Link>
      </header>

      <section
        className={styles.searchPanel}
        aria-labelledby="search-title"
      >
        <h2 id="search-title">Buscar contenido</h2>

        <label
          className={styles.label}
          htmlFor="media-search"
        >
          Título
        </label>

        <input
          className={styles.input}
          id="media-search"
          type="search"
          value={query}
          minLength={2}
          placeholder="Ejemplo: Matrix"
          onChange={(event) => {
            setQuery(event.target.value)
            setPage(1)
          }}
        />

        {normalizedQuery.length === 1 && (
          <p className={styles.hint}>
            Escribe al menos dos caracteres.
          </p>
        )}
      </section>

      {searchQuery.isFetching && (
        <p className={styles.status} role="status">
          Buscando...
        </p>
      )}

      {searchQuery.isError && (
        <p
          className={`${styles.status} ${styles.error}`}
          role="alert"
        >
          No fue posible buscar contenido:{' '}
          {searchQuery.error.message}
        </p>
      )}

      {searchQuery.data && results.length === 0 && (
        <p className={styles.status}>
          No encontramos resultados.
        </p>
      )}

      {results.length > 0 && (
        <section
          className={styles.results}
          aria-label="Resultados de búsqueda"
        >
          <h2>Resultados</h2>

          <div className={styles.grid}>
            {results.map((result) => (
              <article
                className={styles.card}
                key={
                  `${result.media_type}-` +
                  result.tmdb_id
                }
              >
                <div className={styles.posterFrame}>
                  {result.poster_url ? (
                    <img
                      className={styles.poster}
                      src={result.poster_url}
                      alt={`Póster de ${result.title}`}
                      loading="lazy"
                    />
                  ) : (
                    <div
                      className={styles.posterPlaceholder}
                      aria-hidden="true"
                    >
                      Sin póster
                    </div>
                  )}

                  {savedMediaKeys.has(
                    `${result.media_type}-${result.tmdb_id}`,
                  ) && (
                      <span className={styles.savedBadge}>
                        Guardado en tu biblioteca
                      </span>
                    )}
                </div>

                <div className={styles.cardContent}>
                  <h3>
                    <Link
                      className={styles.titleLink}
                      to={
                        `/media/${result.media_type}/` +
                        result.tmdb_id
                      }
                    >
                      {result.title}
                    </Link>
                  </h3>

                  <p className={styles.meta}>
                    {result.media_type === 'movie'
                      ? 'Película'
                      : 'Serie'}
                    {result.release_year
                      ? ` · ${result.release_year}`
                      : ''}
                    {` · ${result.rating.toFixed(1)}/10`}
                  </p>

                  <p className={styles.overview}>
                    {result.overview ||
                      'Sin descripción disponible.'}
                  </p>
                </div>
              </article>
            ))}
          </div>
          {totalPages > 1 && (
            <nav
              className={styles.pagination}
              aria-label="Paginación de resultados"
            >
              <button
                type="button"
                disabled={
                  currentPage <= 1 ||
                  searchQuery.isFetching
                }
                onClick={() => {
                  setPage((currentPageValue) =>
                    Math.max(1, currentPageValue - 1),
                  )
                }}
              >
                ← Anterior
              </button>

              <p>
                Página {currentPage} de {totalPages}
              </p>

              <button
                type="button"
                disabled={
                  currentPage >= totalPages ||
                  searchQuery.isFetching
                }
                onClick={() => {
                  setPage((currentPageValue) =>
                    Math.min(
                      totalPages,
                      currentPageValue + 1,
                    ),
                  )
                }}
              >
                Siguiente →
              </button>
            </nav>
          )}
        </section>
      )}
    </main>
  )
}