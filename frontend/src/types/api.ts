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

export interface Genre {
  id: number
  name: string
}

export interface MediaDetails {
  tmdb_id: number
  media_type: MediaType
  title: string
  original_title: string
  overview: string
  poster_url: string | null
  backdrop_url: string | null
  release_year: number | null
  rating: number
  vote_count: number
  genres: Genre[]
  runtime: number | null
  number_of_seasons: number | null
  number_of_episodes: number | null
}

export type AvailabilityType =
  | 'flatrate'
  | 'free'
  | 'ads'
  | 'rent'
  | 'buy'

export interface WatchProvider {
  tmdb_provider_id: number
  name: string
  logo_url: string | null
  display_priority: number
  availability_type: AvailabilityType
}

export interface WatchProvidersResponse {
  tmdb_id: number
  media_type: MediaType
  region: string
  link: string | null
  providers: WatchProvider[]
}