import type {
  HealthResponse,
  SearchResponse,
} from '../types/api'


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000/api/v1'


async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)

  if (!response.ok) {
    throw new Error(
      `El backend respondió con el código ${response.status}`,
    )
  }

  const data: T = await response.json()

  return data
}


export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/health')
}


export function searchMedia(
  query: string,
  page = 1,
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    page: String(page),
  })

  return requestJson<SearchResponse>(
    `/search?${params.toString()}`,
  )
}