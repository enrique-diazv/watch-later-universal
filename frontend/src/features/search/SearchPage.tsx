import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { searchMedia } from '../../services/api'


export function SearchPage() {
  const [query, setQuery] = useState('')

  const normalizedQuery = query.trim()
  const debouncedQuery = useDebouncedValue(
    normalizedQuery,
    400,
  )

  const canSearch = debouncedQuery.length >= 2

  const searchQuery = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchMedia(debouncedQuery),
    enabled: canSearch,
  })

  const results = searchQuery.data?.results ?? []

  return (
    <main>
      <header>
        <h1>Watch Later Universal</h1>
        <p>Busca películas y series en un solo lugar.</p>
      </header>

      <section aria-labelledby="search-title">
        <h2 id="search-title">Buscar contenido</h2>

        <label htmlFor="media-search">
          Título
        </label>

        <input
          id="media-search"
          type="search"
          value={query}
          minLength={2}
          placeholder="Ejemplo: Matrix"
          onChange={(event) => {
            setQuery(event.target.value)
          }}
        />

        {normalizedQuery.length === 1 && (
          <p>Escribe al menos dos caracteres.</p>
        )}
      </section>

      {searchQuery.isFetching && (
        <p role="status">Buscando...</p>
      )}

      {searchQuery.isError && (
        <p role="alert">
          No fue posible buscar contenido:{' '}
          {searchQuery.error.message}
        </p>
      )}

      {searchQuery.data && results.length === 0 && (
        <p>No encontramos resultados.</p>
      )}

      {results.length > 0 && (
        <section aria-label="Resultados de búsqueda">
          <h2>Resultados</h2>

          {results.map((result) => (
            <article
              key={`${result.media_type}-${result.tmdb_id}`}
            >
              {result.poster_url && (
                <img
                  src={result.poster_url}
                  alt={`Póster de ${result.title}`}
                  width="185"
                  loading="lazy"
                />
              )}

              <div>
                <h3>{result.title}</h3>

                <p>
                  {result.media_type === 'movie'
                    ? 'Película'
                    : 'Serie'}
                  {result.release_year
                    ? ` · ${result.release_year}`
                    : ''}
                  {` · ${result.rating.toFixed(1)}/10`}
                </p>

                <p>
                  {result.overview ||
                    'Sin descripción disponible.'}
                </p>
              </div>
            </article>
          ))}
        </section>
      )}
    </main>
  )
}