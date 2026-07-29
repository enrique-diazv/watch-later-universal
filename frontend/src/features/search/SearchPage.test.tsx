import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { searchMedia } from '../../services/api'
import { renderWithProviders } from '../../tests/test-utils'
import type { SearchResponse } from '../../types/api'
import { SearchPage } from './SearchPage'


vi.mock('../../services/api', () => ({
  searchMedia: vi.fn(),
}))


const mockedSearchMedia = vi.mocked(searchMedia)


const fakeResponse: SearchResponse = {
  page: 1,
  total_pages: 1,
  results: [
    {
      tmdb_id: 603,
      media_type: 'movie',
      title: 'Matrix',
      overview: 'Una hacker descubre la verdad.',
      poster_url: null,
      release_year: 1999,
      rating: 8.2,
      genre_ids: [28, 878],
    },
  ],
}


afterEach(() => {
  vi.clearAllMocks()
})


describe('SearchPage', () => {
  it('searches after the user enters a valid query', async () => {
    mockedSearchMedia.mockResolvedValue(fakeResponse)

    const user = userEvent.setup()

    renderWithProviders(<SearchPage />)

    const input = screen.getByRole('searchbox', {
      name: /título/i,
    })

    await user.type(input, 'm')

    expect(mockedSearchMedia).not.toHaveBeenCalled()

    await user.type(input, 'atrix')

    const resultLink = await screen.findByRole(
      'link',
      {
        name: 'Matrix',
      },
    )

    expect(mockedSearchMedia).toHaveBeenCalledWith(
      'matrix',
    )
    expect(resultLink).toHaveAttribute(
      'href',
      '/media/movie/603',
    )
  })
})