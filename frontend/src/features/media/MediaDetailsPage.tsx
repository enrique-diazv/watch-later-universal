import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { getMediaDetails,
getWatchProviders,
} from '../../services/api'
import type {
  AvailabilityType,
  MediaType,
} from '../../types/api'

const availabilityLabels: Record<
  AvailabilityType,
  string
> = {
  flatrate: 'Suscripción',
  free: 'Gratis',
  ads: 'Gratis con anuncios',
  rent: 'Renta',
  buy: 'Compra',
}

function isMediaType(
  value: string | undefined,
): value is MediaType {
  return value === 'movie' || value === 'tv'
}


export function MediaDetailsPage() {
  const { mediaType, tmdbId } = useParams()

  const validMediaType = isMediaType(mediaType)
  const parsedTmdbId = Number(tmdbId)
  const validTmdbId =
    Number.isInteger(parsedTmdbId) && parsedTmdbId > 0

  const safeMediaType: MediaType = validMediaType
    ? mediaType
    : 'movie'

  const safeTmdbId = validTmdbId
    ? parsedTmdbId
    : 0

  const detailsQuery = useQuery({
    queryKey: [
      'media-details',
      safeMediaType,
      safeTmdbId,
    ],
    queryFn: () =>
      getMediaDetails(safeMediaType, safeTmdbId),
    enabled: validMediaType && validTmdbId,
  })

const providersQuery = useQuery({
  queryKey: [
    'watch-providers',
    safeMediaType,
    safeTmdbId,
  ],
  queryFn: () =>
    getWatchProviders(safeMediaType, safeTmdbId),
  enabled: validMediaType && validTmdbId,
})

  if (!validMediaType || !validTmdbId) {
    return (
      <main>
        <Link to="/">← Volver a la búsqueda</Link>
        <h1>Dirección inválida</h1>
        <p>El tipo o identificador no es válido.</p>
      </main>
    )
  }

  if (detailsQuery.isPending) {
    return (
      <main>
        <Link to="/">← Volver a la búsqueda</Link>
        <p role="status">Cargando detalles...</p>
      </main>
    )
  }

  if (detailsQuery.isError) {
    return (
      <main>
        <Link to="/">← Volver a la búsqueda</Link>
        <h1>No pudimos cargar el contenido</h1>
        <p role="alert">{detailsQuery.error.message}</p>
      </main>
    )
  }

  const media = detailsQuery.data

  return (
    <main>
      <Link to="/">← Volver a la búsqueda</Link>

      {media.backdrop_url && (
        <img
          src={media.backdrop_url}
          alt=""
          width="800"
        />
      )}

      <article>
        {media.poster_url && (
          <img
            src={media.poster_url}
            alt={`Póster de ${media.title}`}
            width="250"
          />
        )}

        <div>
          <p>
            {media.media_type === 'movie'
              ? 'Película'
              : 'Serie'}
          </p>

          <h1>{media.title}</h1>

          {media.original_title !== media.title && (
            <p>Título original: {media.original_title}</p>
          )}

          <p>
            {media.release_year ?? 'Año desconocido'}
            {' · '}
            {media.rating.toFixed(1)}/10
            {' · '}
            {media.vote_count.toLocaleString()} votos
          </p>

          <p>
            {media.genres
              .map((genre) => genre.name)
              .join(' · ') || 'Sin géneros disponibles'}
          </p>

          <p>
            {media.overview ||
              'Sin descripción disponible.'}
          </p>

          {media.media_type === 'movie' &&
            media.runtime !== null && (
              <p>Duración: {media.runtime} minutos</p>
            )}

          {media.media_type === 'tv' && (
            <>
              <p>
                Temporadas:{' '}
                {media.number_of_seasons ?? 'Desconocido'}
              </p>
              <p>
                Episodios:{' '}
                {media.number_of_episodes ?? 'Desconocido'}
              </p>
            </>
          )}
        </div>
      </article>
      <section aria-labelledby="providers-title">
  <h2 id="providers-title">
    Disponible en México
  </h2>

  {providersQuery.isPending && (
    <p role="status">Consultando plataformas...</p>
  )}

  {providersQuery.isError && (
    <p role="alert">
      No fue posible consultar las plataformas.
    </p>
  )}

  {providersQuery.data &&
    providersQuery.data.providers.length === 0 && (
      <p>
        No hay información de disponibilidad para México.
      </p>
    )}

  {providersQuery.data &&
    providersQuery.data.providers.length > 0 && (
      <ul>
        {providersQuery.data.providers.map(
          (provider) => (
            <li
              key={
                `${provider.tmdb_provider_id}-` +
                provider.availability_type
              }
            >
              {provider.logo_url && (
                <img
                  src={provider.logo_url}
                  alt=""
                  width="40"
                  loading="lazy"
                />
              )}

              <span>{provider.name}</span>
              {' — '}
              <span>
                {
                  availabilityLabels[
                    provider.availability_type
                  ]
                }
              </span>
            </li>
          ),
        )}
      </ul>
    )}

  {providersQuery.data && (
    <footer>
      <p>
        Información de disponibilidad proporcionada
        por JustWatch.
      </p>

      {providersQuery.data.link && (
        <a
          href={providersQuery.data.link}
          target="_blank"
          rel="noreferrer"
        >
          Consultar disponibilidad en TMDB
        </a>
      )}
    </footer>
  )}
</section>
    </main>
  )
}