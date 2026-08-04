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

export interface User {
  id: string
  email: string
  display_name: string
  country_code: string
  is_active: boolean
  is_email_verified: boolean
  created_at: string
  updated_at: string
}


export interface RegisterPayload {
  email: string
  password: string
  display_name: string
  country_code: string
}


export interface LoginPayload {
  email: string
  password: string
}

export interface EmailVerificationConfirmPayload {
  token: string
}


export interface EmailVerificationResendPayload {
  email: string
}

export interface PasswordResetRequestPayload {
  email: string
}

export interface PasswordResetConfirmPayload {
  token: string
  new_password: string
}

export interface MessageResponse {
  message: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}


export type LibraryStatus =
  | 'plan_to_watch'
  | 'watching'
  | 'completed'
  | 'paused'
  | 'dropped'


export interface LibraryMedia {
  id: string
  tmdb_id: number
  media_type: MediaType
  title: string
  original_title: string | null
  overview: string | null
  poster_path: string | null
  backdrop_path: string | null
  release_date: string | null
  tmdb_rating: number
  vote_count: number
  runtime: number | null
}


export interface LibraryItem {
  id: string
  status: LibraryStatus
  user_rating: number | null
  is_favorite: boolean
  notes: string | null
  added_at: string
  started_at: string | null
  completed_at: string | null
  updated_at: string
  media: LibraryMedia
}


export interface AddLibraryItemPayload {
  tmdb_id: number
  media_type: MediaType
  status?: LibraryStatus
}


export interface UpdateLibraryItemPayload {
  status?: LibraryStatus
  user_rating?: number | null
  is_favorite?: boolean
  notes?: string | null
}