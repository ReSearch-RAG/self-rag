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
  is_conversational?: boolean
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  isSufficient?: boolean
  attempts?: number
  isConversational?: boolean
}

export interface ChatHistoryMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  is_sufficient?: boolean | null
  attempts?: number | null
}

export interface ChatHistoryResponse {
  document_id: number
  messages: ChatHistoryMessage[]
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

/* Dashboard Conversations */

export interface ConversationSummary {
  conversation_id: number
  document_id: number
  document_name: string
  title: string
  preview: string
  updated_at: string
  message_count: number
}

export interface ConversationListResponse {
  conversations: ConversationSummary[]
}