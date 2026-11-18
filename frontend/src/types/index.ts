export type Page = 'dashboard' | 'chat' | 'documents'

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

/* Auth */

export interface User {
  id: number
  email: string
  name: string
}

export interface AuthTokenResponse {
  access_token: string
  token_type: string
}

export interface RegisterPayload {
  email: string
  name: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}