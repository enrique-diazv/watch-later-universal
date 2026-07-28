export interface HealthResponse {
  status: string
  service: string
}

export type MediaType = 'movie' | 'tv'

export interface SearchResult {
  tmdb_id: number
  media_type: MediaType
  title: string
  overview: string
  poster_url: string | null
  release_year: number | null
  rating: number
  genre_ids: number[]
}

export interface SearchResponse {
  page: number
  total_pages: number
  results: SearchResult[]
}