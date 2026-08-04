import type {
  EmailVerificationConfirmPayload,
  EmailVerificationResendPayload,
  MessageResponse,
  HealthResponse,
  MediaDetails,
  MediaType,
  SearchResponse,
  WatchProvidersResponse,
  LoginPayload,
  PasswordResetConfirmPayload,
  PasswordResetRequestPayload,
  RegisterPayload,
  TokenResponse,
  User,
  AddLibraryItemPayload,
  LibraryItem,
  UpdateLibraryItemPayload,
} from '../types/api'


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  'http://localhost:8000/api/v1'

let accessToken: string | null = null


export function setAccessToken(
  token: string | null,
) {
  accessToken = token
}


export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)

    this.name = 'ApiError'
    this.status = status
  }
}


interface RequestOptions
  extends Omit<RequestInit, 'body'> {
  body?: unknown
  authenticated?: boolean
}


async function requestJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    authenticated = false,
    body,
    headers: initialHeaders,
    ...requestOptions
  } = options

  const headers = new Headers(initialHeaders)

  if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (authenticated && accessToken) {
    headers.set(
      'Authorization',
      `Bearer ${accessToken}`,
    )
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...requestOptions,
      headers,
      credentials: 'include',
      body:
        body === undefined
          ? undefined
          : JSON.stringify(body),
    },
  )

  if (!response.ok) {
    let message = (
      `El backend respondió con el código ` +
      response.status
    )

    try {
      const errorBody = (
        await response.json()
      ) as {
        detail?: unknown
      }

      if (typeof errorBody.detail === 'string') {
        message = errorBody.detail
      }
    } catch {
      // Algunas respuestas de error no contienen JSON.
    }

    throw new ApiError(response.status, message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
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


export function getMediaDetails(
  mediaType: MediaType,
  tmdbId: number,
): Promise<MediaDetails> {
  return requestJson<MediaDetails>(
    `/media/${mediaType}/${tmdbId}`,
  )
}


export function getWatchProviders(
  mediaType: MediaType,
  tmdbId: number,
): Promise<WatchProvidersResponse> {
  return requestJson<WatchProvidersResponse>(
    `/media/${mediaType}/${tmdbId}/providers`,
  )
}

export function registerUser(
  payload: RegisterPayload,
): Promise<User> {
  return requestJson<User>(
    '/auth/register',
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function verifyEmail(
  payload: EmailVerificationConfirmPayload,
): Promise<MessageResponse> {
  return requestJson<MessageResponse>(
    '/auth/verify-email',
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function resendVerificationEmail(
  payload: EmailVerificationResendPayload,
): Promise<MessageResponse> {
  return requestJson<MessageResponse>(
    '/auth/resend-verification',
    {
      method: 'POST',
      body: payload,
    },
  )
}
export function requestPasswordReset(
  payload: PasswordResetRequestPayload,
): Promise<MessageResponse> {
  return requestJson<MessageResponse>(
    '/auth/forgot-password',
    {
      method: 'POST',
      body: payload,
    },
  )
}

export function resetPassword(
  payload: PasswordResetConfirmPayload,
): Promise<MessageResponse> {
  return requestJson<MessageResponse>(
    '/auth/reset-password',
    {
      method: 'POST',
      body: payload,
    },
  )
}

export async function loginUser(
  payload: LoginPayload,
): Promise<TokenResponse> {
  const tokenResponse = (
    await requestJson<TokenResponse>(
      '/auth/login',
      {
        method: 'POST',
        body: payload,
      },
    )
  )

  setAccessToken(tokenResponse.access_token)

  return tokenResponse
}


export async function refreshSession(
): Promise<TokenResponse> {
  try {
    const tokenResponse = (
      await requestJson<TokenResponse>(
        '/auth/refresh',
        {
          method: 'POST',
        },
      )
    )

    setAccessToken(tokenResponse.access_token)

    return tokenResponse
  } catch (error) {
    setAccessToken(null)
    throw error
  }
}


export async function logoutSession(): Promise<void> {
  try {
    await requestJson<void>(
      '/auth/logout',
      {
        method: 'POST',
      },
    )
  } finally {
    setAccessToken(null)
  }
}


export function getCurrentUser(): Promise<User> {
  return requestJson<User>(
    '/auth/me',
    {
      authenticated: true,
    },
  )
}

export function getLibraryItems(
): Promise<LibraryItem[]> {
  return requestJson<LibraryItem[]>(
    '/library',
    {
      authenticated: true,
    },
  )
}


export function addLibraryItem(
  payload: AddLibraryItemPayload,
): Promise<LibraryItem> {
  return requestJson<LibraryItem>(
    '/library',
    {
      method: 'POST',
      authenticated: true,
      body: payload,
    },
  )
}


export function updateLibraryItem(
  itemId: string,
  payload: UpdateLibraryItemPayload,
): Promise<LibraryItem> {
  return requestJson<LibraryItem>(
    `/library/${encodeURIComponent(itemId)}`,
    {
      method: 'PATCH',
      authenticated: true,
      body: payload,
    },
  )
}


export function deleteLibraryItem(
  itemId: string,
): Promise<void> {
  return requestJson<void>(
    `/library/${encodeURIComponent(itemId)}`,
    {
      method: 'DELETE',
      authenticated: true,
    },
  )
}