import type {
  AuthTokenResponse,
  ChatResponse,
  Document,
  HealthResponse,
  LoginPayload,
  RegisterPayload,
  User,
} from '../types'

const apiBaseUrl = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function formatErrorDetail(detail: unknown): string | undefined {
  if (typeof detail === 'string') {
    return detail
  }

  if (!Array.isArray(detail)) {
    return undefined
  }

  const messages = detail.flatMap((item) => {
    if (!isRecord(item) || typeof item.msg !== 'string') {
      return []
    }

    const location = Array.isArray(item.loc)
      ? item.loc.filter((part): part is string | number =>
          typeof part === 'string' || typeof part === 'number',
        )
      : []
    const field = location.length > 0 ? `${location.join('.')}: ` : ''
    return [`${field}${item.msg}`]
  })

  return messages.length > 0 ? messages.join('; ') : undefined
}

function getErrorMessage(payload: unknown): string | undefined {
  if (typeof payload === 'string' && payload.length > 0) {
    return payload
  }

  if (isRecord(payload) && 'detail' in payload) {
    return formatErrorDetail(payload.detail)
  }

  return undefined
}

async function request<T>(
  path: string,
  options?: RequestInit,
  token?: string,
): Promise<T> {
  let response: Response

  const headers: Record<string, string> = {}

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // Merge caller-supplied headers without overwriting the auth header
  if (options?.headers) {
    const incoming = options.headers as Record<string, string>
    Object.assign(headers, incoming)
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers,
    })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw error
    }
    throw new Error(
      'Unable to reach the backend. Check that it is running and VITE_API_URL is configured.',
      { cause: error },
    )
  }

  const body = await response.text()
  let payload: unknown

  if (body.length > 0) {
    try {
      payload = JSON.parse(body) as unknown
    } catch {
      payload = body
    }
  }

  if (!response.ok) {
    const detail = getErrorMessage(payload)
    throw new Error(
      detail
        ? `Backend request failed (${response.status}): ${detail}`
        : `Backend request failed with status ${response.status}.`,
    )
  }

  if (payload === undefined) {
    throw new Error('The backend returned an empty response.')
  }

  if (typeof payload === 'string') {
    throw new Error('The backend returned an invalid JSON response.')
  }

  return payload as T
}

/* ── Public API helpers ────────────────────────────────────────── */

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export function register(payload: RegisterPayload): Promise<User> {
  return request<User>('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function login(payload: LoginPayload): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getMe(token: string): Promise<User> {
  return request<User>('/auth/me', {}, token)
}

export function getDocuments(token: string): Promise<Document[]> {
  return request<Document[]>('/documents/', {}, token)
}

export function uploadDocument(file: File, token: string): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)

  return request<Document>(
    '/documents/upload',
    { method: 'POST', body: formData },
    token,
  )
}

export function sendChatMessage(
  documentId: number,
  message: string,
  token: string,
): Promise<ChatResponse> {
  return request<ChatResponse>(
    '/chat/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, message }),
    },
    token,
  )
}
