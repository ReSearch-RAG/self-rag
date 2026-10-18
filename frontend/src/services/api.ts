import type {
  ChatResponse,
  Document,
  HealthResponse,
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
): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${apiBaseUrl}${path}`, options)
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

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export function getDocuments(): Promise<Document[]> {
  return request<Document[]>('/documents/')
}

export function uploadDocument(file: File, userId: number): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', String(userId))

  return request<Document>('/documents/upload', {
    method: 'POST',
    body: formData,
  })
}

export function sendChatMessage(
  documentId: number,
  message: string,
): Promise<ChatResponse> {
  return request<ChatResponse>('/chat/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ document_id: documentId, message }),
  })
}
