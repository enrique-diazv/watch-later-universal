import type { HealthResponse } from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000/api/v1'

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error(
      `El backend respondió con el código ${response.status}`,
    )
  }

  const data: HealthResponse = await response.json()

  return data
}