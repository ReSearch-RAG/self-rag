export type Page = 'chat' | 'documents'

export type ApiStatus = 'checking' | 'online' | 'offline'

export interface HealthResponse {
  status: string
  service: string
}

export interface Document {
  id: number
  filename: string
  file_type: string
  status: string
  created_at: string
}

export interface ChatResponse {
  document_id: number
  message: string
  answer: string
  is_sufficient: boolean
  attempts: number
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  isSufficient?: boolean
  attempts?: number
}