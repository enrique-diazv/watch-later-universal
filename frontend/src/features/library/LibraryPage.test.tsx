import {
  screen,
  waitFor,
  within,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import {
  deleteLibraryItem,
  getLibraryItems,
  updateLibraryItem,
} from '../../services/api'
import { renderWithProviders } from '../../tests/test-utils'
import type {
  LibraryItem,
  User,
} from '../../types/api'
import { LibraryPage } from './LibraryPage'


vi.mock('../../services/api', () => ({
  getLibraryItems: vi.fn(),
  updateLibraryItem: vi.fn(),
  deleteLibraryItem: vi.fn(),
}))


const mockedGetLibraryItems = vi.mocked(
  getLibraryItems,
)
const mockedUpdateLibraryItem = vi.mocked(
  updateLibraryItem,
)
const mockedDeleteLibraryItem = vi.mocked(
  deleteLibraryItem,
)


const fakeUser: User = {
  id: 'user-1',
  email: 'learner@example.com',
  display_name: 'Learner',
  country_code: 'MX',
  is_active: true,
  is_email_verified: true,
  created_at: '2026-08-03T00:00:00Z',
  updated_at: '2026-08-03T00:00:00Z',
}


const fakeLibraryItem: LibraryItem = {
  id: 'library-item-1',
  status: 'plan_to_watch',
  user_rating: null,
  is_favorite: false,
  notes: null,
  added_at: '2026-08-03T00:00:00Z',
  started_at: null,
  completed_at: null,
  updated_at: '2026-08-03T00:00:00Z',
  media: {
    id: 'media-1',
    tmdb_id: 603,
    media_type: 'movie',
    title: 'Matrix',
    original_title: 'The Matrix',
    overview: 'Una hacker descubre la verdad.',
    poster_path: null,
    backdrop_path: null,
    release_date: '1999-03-31',
    tmdb_rating: 8.2,
    vote_count: 28000,
    runtime: 136,
  },
}

const completedFavoriteItem: LibraryItem = {
  ...fakeLibraryItem,
  id: 'library-item-2',
  status: 'completed',
  is_favorite: true,
  updated_at: '2026-08-04T00:00:00Z',
  media: {
    ...fakeLibraryItem.media,
    id: 'media-2',
    tmdb_id: 329865,
    title: 'Arrival',
    original_title: 'Arrival',
  },
}

function renderLibrary() {
  return renderWithProviders(
    <LibraryPage />,
    {
      auth: {
        user: fakeUser,
        isAuthenticated: true,
      },
    },
  )
}


afterEach(() => {
  vi.clearAllMocks()
})


describe('LibraryPage', () => {
  it('updates the viewing status', async () => {
    mockedGetLibraryItems.mockResolvedValue([
      fakeLibraryItem,
    ])
    mockedUpdateLibraryItem.mockResolvedValue({
      ...fakeLibraryItem,
      status: 'completed',
    })

    const user = userEvent.setup()

    renderLibrary()

    expect(
      await screen.findByRole('link', {
        name: 'Matrix',
      }),
    ).toBeVisible()

    const libraryGrid = within(
      screen.getByRole('region', {
        name: 'Contenido guardado',
      }),
    )

    await user.selectOptions(
      libraryGrid.getByRole('combobox', {
        name: 'Estado',
      }),
      'completed',
    )

    await waitFor(() => {
      expect(
        mockedUpdateLibraryItem,
      ).toHaveBeenCalledWith(
        'library-item-1',
        {
          status: 'completed',
        },
      )
    })
  })

  it('marks an item as favorite', async () => {
    mockedGetLibraryItems.mockResolvedValue([
      fakeLibraryItem,
    ])
    mockedUpdateLibraryItem.mockResolvedValue({
      ...fakeLibraryItem,
      is_favorite: true,
    })

    const user = userEvent.setup()

    renderLibrary()

    await user.click(
      await screen.findByRole('button', {
        name: /favorito/i,
      }),
    )

    expect(
      mockedUpdateLibraryItem,
    ).toHaveBeenCalledWith(
      'library-item-1',
      {
        is_favorite: true,
      },
    )
  })

  it('saves a rating selected by half stars', async () => {
    mockedGetLibraryItems.mockResolvedValue([
      fakeLibraryItem,
    ])
    mockedUpdateLibraryItem.mockResolvedValue({
      ...fakeLibraryItem,
      user_rating: 7,
    })

    const user = userEvent.setup()

    renderLibrary()

    await user.click(
      await screen.findByRole('button', {
        name: 'Editar calificación',
      }),
    )

    await user.click(
      screen.getByRole('button', {
        name: 'Calificar con 3.5 estrellas',
      }),
    )

    await user.click(
      screen.getByRole('button', {
        name: 'Guardar calificación',
      }),
    )

    await waitFor(() => {
      expect(
        mockedUpdateLibraryItem,
      ).toHaveBeenCalledWith(
        'library-item-1',
        {
          user_rating: 7,
        },
      )
    })
  })

  it('filters the library by status', async () => {
    mockedGetLibraryItems.mockResolvedValue([
      fakeLibraryItem,
      completedFavoriteItem,
    ])

    const user = userEvent.setup()

    renderLibrary()

    expect(
      await screen.findByRole('link', {
        name: 'Matrix',
      }),
    ).toBeVisible()
    expect(
      screen.getByRole('link', {
        name: 'Arrival',
      }),
    ).toBeVisible()

    const filters = within(
      screen.getByRole('region', {
        name: 'Filtros de biblioteca',
      }),
    )

    await user.selectOptions(
      filters.getByRole('combobox', {
        name: 'Estado',
      }),
      'completed',
    )

    expect(
      screen.queryByRole('link', {
        name: 'Matrix',
      }),
    ).not.toBeInTheDocument()
    expect(
      screen.getByRole('link', {
        name: 'Arrival',
      }),
    ).toBeVisible()
    expect(
      filters.getByText('1 elemento'),
    ).toBeVisible()

    await user.click(
      filters.getByRole('button', {
        name: 'Limpiar filtros',
      }),
    )

    expect(
      await screen.findByRole('link', {
        name: 'Matrix',
      }),
    ).toBeVisible()
  })

  it('sorts the library alphabetically', async () => {
    mockedGetLibraryItems.mockResolvedValue([
      fakeLibraryItem,
      completedFavoriteItem,
    ])

    const user = userEvent.setup()

    renderLibrary()

    const filters = within(
      await screen.findByRole('region', {
        name: 'Filtros de biblioteca',
      }),
    )

    await user.selectOptions(
      filters.getByRole('combobox', {
        name: 'Ordenar',
      }),
      'title',
    )

    const libraryGrid = within(
      screen.getByRole('region', {
        name: 'Contenido guardado',
      }),
    )

    await waitFor(() => {
      const titles = libraryGrid
        .getAllByRole('link')
        .map((link) => link.textContent)

      expect(titles).toEqual([
        'Arrival',
        'Matrix',
      ])
    })
  })

  it('removes an item from the library', async () => {
    mockedGetLibraryItems.mockResolvedValue([
      fakeLibraryItem,
    ])
    mockedDeleteLibraryItem.mockResolvedValue(
      undefined,
    )

    const user = userEvent.setup()

    renderLibrary()

    await user.click(
      await screen.findByRole('button', {
        name: 'Quitar',
      }),
    )

    expect(
      mockedDeleteLibraryItem,
    ).toHaveBeenCalledWith(
      'library-item-1',
    )
  })
})