import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import {
  getMediaDetails,
  getWatchProviders,
} from '../../services/api'
import type {
  AvailabilityType,
  MediaType,
} from '../../types/api'
import styles from './MediaDetailsPage.module.css'


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
      <main
        className={`${styles.page} ${styles.statusPage}`}
      >
        <Link className={styles.backLink} to="/">
          ← Volver a la búsqueda
        </Link>
        <h1>Dirección inválida</h1>
        <p>El tipo o identificador no es válido.</p>
      </main>
    )
  }

  if (detailsQuery.isPending) {
    return (
      <main
        className={`${styles.page} ${styles.statusPage}`}
      >
        <Link className={styles.backLink} to="/">
          ← Volver a la búsqueda
        </Link>
        <p role="status">Cargando detalles...</p>
      </main>
    )
  }

  if (detailsQuery.isError) {
    return (
      <main
        className={`${styles.page} ${styles.statusPage}`}
      >
        <Link className={styles.backLink} to="/">
          ← Volver a la búsqueda
        </Link>
        <h1>No pudimos cargar el contenido</h1>
        <p className={styles.error} role="alert">
          {detailsQuery.error.message}
        </p>
      </main>
    )
  }

  const media = detailsQuery.data

  return (
    <main className={styles.page}>
      <Link className={styles.backLink} to="/">
        ← Volver a la búsqueda
      </Link>

      <section className={styles.hero}>
        {media.backdrop_url && (
          <img
            className={styles.heroBackdrop}
            src={media.backdrop_url}
            alt=''
            />
        )}

        <div
          className={styles.heroShade}
          aria-hidden="true"
          />
        
        <article className={styles.content}>

        {media.poster_url && (
          <img
            className={styles.poster}
            src={media.poster_url}
            alt={`Póster de ${media.title}`}
          />
        )}

        <div className={styles.details}>
          <p className={styles.eyebrow}>
            {media.media_type === 'movie'
              ? 'Película'
              : 'Serie'}
          </p>

          <h1 className={styles.title}>{media.title}</h1>

          {media.original_title &&
            media.original_title !== media.title && (
              <p className={styles.originalTitle}>
                Título original: {media.original_title}
              </p>
            )}

          <p className={styles.meta}>
            {media.release_year ?? 'Año desconocido'}
            {' · '}
            {media.rating.toFixed(1)}/10
            {' · '}
            {media.vote_count.toLocaleString('es-MX')}
            {' votos'}
          </p>

          {media.genres.length > 0 && (
            <ul className={styles.genres}>
              {media.genres.map((genre) => (
                <li className={styles.genre} key={genre.id}>
                  {genre.name}
                </li>
              ))}
            </ul>
          )}

          <p className={styles.overview}>
            {media.overview ||
              'Sin descripción disponible.'}
          </p>

          <div className={styles.facts}>
            {media.media_type === 'movie' &&
              media.runtime !== null && (
                <span className={styles.fact}>
                  {media.runtime} minutos
                </span>
              )}

            {media.media_type === 'tv' && (
              <>
                <span className={styles.fact}>
                  {media.number_of_seasons ?? '?'} temporadas
                </span>
                <span className={styles.fact}>
                  {media.number_of_episodes ?? '?'} episodios
                </span>
              </>
            )}
          </div>
        </div>
      </article>
      </section>        
      <section
        className={styles.providers}
        aria-labelledby="providers-title"
      >
        <h2 id="providers-title">
          Disponible en México
        </h2>

        {providersQuery.isPending && (
          <p role="status">Consultando plataformas...</p>
        )}

        {providersQuery.isError && (
          <p className={styles.error} role="alert">
            No fue posible consultar las plataformas.
          </p>
        )}

        {providersQuery.data &&
          providersQuery.data.providers.length === 0 && (
            <p>
              No hay información de disponibilidad para
              México.
            </p>
          )}

        {providersQuery.data &&
          providersQuery.data.providers.length > 0 && (
            <ul className={styles.providerList}>
              {providersQuery.data.providers.map(
                (provider) => (
                  <li
                    className={styles.provider}
                    key={
                      `${provider.tmdb_provider_id}-` +
                      provider.availability_type
                    }
                  >
                    {provider.logo_url ? (
                      <img
                        className={styles.providerLogo}
                        src={provider.logo_url}
                        alt=""
                        loading="lazy"
                      />
                    ) : (
                      <span
                        className={
                          styles.providerLogoPlaceholder
                        }
                        aria-hidden="true"
                      />
                    )}

                    <span>
                      <span className={styles.providerName}>
                        {provider.name}
                      </span>
                      <span className={styles.providerType}>
                        {
                          availabilityLabels[
                            provider.availability_type
                          ]
                        }
                      </span>
                    </span>
                  </li>
                ),
              )}
            </ul>
          )}

        {providersQuery.data && (
          <footer className={styles.attribution}>
            <p>
              Información de disponibilidad proporcionada
              por JustWatch.
            </p>

            {providersQuery.data.link && (
              <a
                className={styles.externalLink}
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