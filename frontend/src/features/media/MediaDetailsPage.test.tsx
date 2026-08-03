import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import {
  addLibraryItem,
  getMediaDetails,
  getWatchProviders,
  getLibraryItems,
} from '../../services/api'
import { renderWithProviders } from '../../tests/test-utils'
import type {
  LibraryItem,
  MediaDetails,
  WatchProvidersResponse,
} from '../../types/api'
import { MediaDetailsPage } from './MediaDetailsPage'


vi.mock('../../services/api', () => ({
  addLibraryItem: vi.fn(),
  getLibraryItems: vi.fn(),
  getMediaDetails: vi.fn(),
  getWatchProviders: vi.fn(),
}))

const mockedLibrary = vi.mocked(
  getLibraryItems,
)

const mockedAddLibraryItem = vi.mocked(
  addLibraryItem,
)
const mockedDetails = vi.mocked(getMediaDetails)
const mockedProviders = vi.mocked(getWatchProviders)


const fakeMovie: MediaDetails = {
  tmdb_id: 603,
  media_type: 'movie',
  title: 'Matrix',
  original_title: 'The Matrix',
  overview: 'Una hacker descubre la verdad.',
  poster_url: null,
  backdrop_url: null,
  release_year: 1999,
  rating: 8.2,
  vote_count: 27000,
  genres: [
    {
      id: 878,
      name: 'Ciencia ficción',
    },
  ],
  runtime: 136,
  number_of_seasons: null,
  number_of_episodes: null,
}


const fakeProviders: WatchProvidersResponse = {
  tmdb_id: 603,
  media_type: 'movie',
  region: 'MX',
  link: 'https://www.themoviedb.org/movie/603/watch',
  providers: [
    {
      tmdb_provider_id: 8,
      name: 'Netflix',
      logo_url: null,
      display_priority: 1,
      availability_type: 'flatrate',
    },
  ],
}

const fakeLibraryItem = {
  id: 'library-item-1',
  status: 'plan_to_watch',
  media: {
    tmdb_id: 603,
    media_type: 'movie',
  },
} as LibraryItem

function renderDetailsPage(

  route: string,
  isAuthenticated = false,
) {
  return renderWithProviders(
    <Routes>
      <Route
        path="/media/:mediaType/:tmdbId"
        element={<MediaDetailsPage />}
      />
      <Route
        path="/library"
        element={<p>Biblioteca personal</p>}
      />
    </Routes>,
    {
      route,
      auth: {
        isAuthenticated,
      },
    },
  )
}

afterEach(() => {
  vi.resetAllMocks()
})


describe('MediaDetailsPage', () => {
  it('adds media to Watch Later', async () => {
  const user = userEvent.setup()

  mockedLibrary.mockResolvedValue([])
  mockedDetails.mockResolvedValue(fakeMovie)
  mockedProviders.mockResolvedValue(fakeProviders)
  mockedAddLibraryItem.mockResolvedValue(
  fakeLibraryItem,
)

  renderDetailsPage(
    '/media/movie/603',
    true,
  )

  await screen.findByRole('heading', {
    level: 1,
    name: 'Matrix',
  })

  await user.click(
    screen.getByRole('button', {
      name: 'Guardar para después',
    }),
  )

  await waitFor(() => {
    expect(mockedAddLibraryItem).toHaveBeenCalledWith({
      tmdb_id: 603,
      media_type: 'movie',
      status: 'plan_to_watch',
    })
  })

  expect(
    await screen.findByText(
      'Ya está en tu lista Watch Later.',
    ),
  ).toBeInTheDocument()
})
  it('shows details and providers', async () => {
    mockedDetails.mockResolvedValue(fakeMovie)
    mockedProviders.mockResolvedValue(fakeProviders)

    renderDetailsPage('/media/movie/603')

    expect(
      await screen.findByRole('heading', {
        level: 1,
        name: 'Matrix',
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByText('Ciencia ficción'),
    ).toBeInTheDocument()

    expect(
      screen.getByText('136 minutos'),
    ).toBeInTheDocument()

    expect(
      await screen.findByText('Netflix'),
    ).toBeInTheDocument()

    expect(
      screen.getByText('Suscripción'),
    ).toBeInTheDocument()

    expect(mockedDetails).toHaveBeenCalledWith(
      'movie',
      603,
    )
    expect(mockedProviders).toHaveBeenCalledWith(
      'movie',
      603,
    )
  })

  it('rejects invalid route parameters', () => {
    renderDetailsPage('/media/person/603')

    expect(
      screen.getByRole('heading', {
        name: 'Dirección inválida',
      }),
    ).toBeInTheDocument()

    expect(mockedDetails).not.toHaveBeenCalled()
    expect(mockedProviders).not.toHaveBeenCalled()
  })
})

it('keeps saved state and navigates to library', async () => {
  const user = userEvent.setup()

  mockedDetails.mockResolvedValue(fakeMovie)
  mockedProviders.mockResolvedValue(fakeProviders)
  mockedLibrary.mockResolvedValue([
    fakeLibraryItem,
  ])

  renderDetailsPage(
    '/media/movie/603',
    true,
  )

  const libraryButton = await screen.findByRole(
    'button',
    {
      name: 'Ir a tu biblioteca',
    },
  )

  expect(
    screen.getByText(
      'Ya está en tu lista Watch Later.',
    ),
  ).toBeInTheDocument()

  await user.click(libraryButton)

  expect(
    await screen.findByText(
      'Biblioteca personal',
    ),
  ).toBeInTheDocument()

  expect(
    mockedAddLibraryItem,
  ).not.toHaveBeenCalled()
})