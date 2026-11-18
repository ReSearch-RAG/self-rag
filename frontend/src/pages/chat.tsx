import { useEffect, useRef, useState } from 'react'
import { getChatHistory, sendChatMessage } from '../services/api'
import { useAuth } from '../context/AuthContext'
import type { ChatMessage, Document } from '../types'

interface ChatPageProps {
  selectedDocument: Document | null
  onBrowseDocuments: () => void
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'An unexpected error occurred.'
}

interface ToastItem {
  id: number
  message: string
  type: 'error' | 'success'
}

export function ChatPage({ selectedDocument, onBrowseDocuments }: ChatPageProps) {
  const { token } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const requestInProgress = useRef(false)
  const nextMessageId = useRef(0)
  const nextToastId = useRef(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const canChat = selectedDocument?.status === 'processed'

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

  function addToast(message: string, type: ToastItem['type'] = 'error') {
    const id = ++nextToastId.current
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => {
      setToasts((t) => t.filter((item) => item.id !== id))
    }, 5000)
  }

  // Auto-resize textarea
  function handleDraftChange(value: string) {
    setDraft(value)
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`
    }
  }

  async function submitMessage() {
    const message = draft.trim()
    if (!message || !selectedDocument || !canChat || requestInProgress.current || !token) {
      return
    }

    requestInProgress.current = true
    setDraft('')
    setIsSending(true)

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    setMessages((current) => [
      ...current,
      { id: ++nextMessageId.current, role: 'user', content: message },
    ])

    try {
      const response = await sendChatMessage(selectedDocument.id, message, token)
      setMessages((current) => [
        ...current,
        {
          id: ++nextMessageId.current,
          role: 'assistant',
          content: response.answer,
          isSufficient: response.is_sufficient,
          attempts: response.attempts,
          isConversational: response.is_conversational,
        },
      ])
    } catch (requestError) {
      addToast(getMessage(requestError), 'error')
    } finally {
      requestInProgress.current = false
      setIsSending(false)
    }
  }

  // Load persisted history whenever the selected document changes
  useEffect(() => {
    if (!selectedDocument || !token) {
      setMessages([])
      return
    }

    let active = true
    nextMessageId.current = 0
    setMessages([])

    getChatHistory(selectedDocument.id, token)
      .then((history) => {
        if (!active) return
        const restored = history.messages.map((item) => ({
          id: ++nextMessageId.current,
          role: item.role,
          content: item.content,
          isSufficient:
            item.is_sufficient === null || item.is_sufficient === undefined
              ? undefined
              : item.is_sufficient,
          attempts:
            item.attempts === null || item.attempts === undefined
              ? undefined
              : item.attempts,
          isConversational:
            item.role === 'assistant' && item.attempts === 0,
        }))
        setMessages(restored)
      })
      .catch((error) => {
        if (active) addToast(getMessage(error), 'error')
      })

    return () => {
      active = false
    }
  }, [selectedDocument, token])

  return (
    <section aria-label="Chat workspace" className="page-content">
      {messages.length === 0 ? (
        <div className="chat-empty-state">
          <div className="empty-state-mark" aria-hidden="true">
            <svg className="header-icon" viewBox="0 0 24 24">
              <path d="M4 5.5h16v11H9l-5 3z" />
              <path d="M8 10h8M8 13.5h5" />
            </svg>
          </div>
          <div className="empty-state-eyebrow">Self-RAG</div>
          <h1 className="empty-state-title" id="chat-title">
            A clear place to begin.
          </h1>
          <p className="empty-state-description">
            {canChat
              ? `Ask a question grounded in ${selectedDocument.filename}.`
              : 'Choose a processed document to start a conversation grounded in its content.'}
          </p>
          {!selectedDocument && (
            <button
              className="primary-button browse-button"
              id="browse-documents-button"
              onClick={onBrowseDocuments}
              type="button"
            >
              Browse documents
            </button>
          )}
          {selectedDocument && !canChat && (
            <div className="backend-note">
              <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 11v5M12 8h.01" />
              </svg>
              <span>
                {selectedDocument.filename} is {selectedDocument.status}.
                Chat is available only when the backend reports the document as processed.
              </span>
            </div>
          )}
        </div>
      ) : (
        <div aria-label="Conversation" className="chat-messages" role="log">
          {messages.map((message) => (
            <article
              className={`chat-message chat-message--${message.role}`}
              key={message.id}
            >
              <div className="chat-message-role">
                {message.role === 'user' ? 'You' : 'Self-RAG'}
              </div>
              <p>{message.content}</p>
              {message.role === 'assistant' && !message.isConversational && (
                <div
                  className={`answer-evidence answer-evidence--${message.isSufficient ? 'sufficient' : 'insufficient'}`}
                >
                  <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24" style={{ width: 13, height: 13, flex: '0 0 auto' }}>
                    {message.isSufficient
                      ? <path d="M20 6L9 17l-5-5" />
                      : <><path d="M12 9v4"/><path d="M12 17h.01"/><circle cx="12" cy="12" r="9"/></>}
                  </svg>
                  {message.isSufficient
                    ? 'Evidence evaluated as sufficient'
                    : 'Insufficient evidence — not a verified answer'}
                  {message.attempts !== undefined &&
                    ` · ${message.attempts} retrieval ${message.attempts === 1 ? 'attempt' : 'attempts'}`}
                </div>
              )}
            </article>
          ))}

          {/* Typing indicator */}
          {isSending && (
            <div className="typing-indicator" aria-live="polite" aria-label="Thinking…">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Composer */}
      <div className="composer-area">
        {selectedDocument && (
          <p className="active-document">
            <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24" style={{ width: 13, height: 13 }}>
              <path d="M5 3.75h9l5 5v11.5H5z" />
              <path d="M14 3.75v5h5M8.5 13h7M8.5 16.5h7" />
            </svg>
            <strong>{selectedDocument.filename}</strong>
          </p>
        )}
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault()
            void submitMessage()
          }}
        >
          <textarea
            aria-label="Message"
            className="composer-input"
            disabled={!canChat || isSending}
            id="chat-input"
            onChange={(e) => handleDraftChange(e.currentTarget.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void submitMessage()
              }
            }}
            placeholder={canChat ? 'Ask about this document…' : 'Select a processed document'}
            maxLength={4000}
            ref={textareaRef}
            rows={1}
            value={draft}
          />
          <button
            aria-label="Send message"
            className="composer-action"
            disabled={!canChat || isSending || !draft.trim()}
            id="chat-send-button"
            type="submit"
          >
            <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
              <path d="m5 12 14-7-4 14-3.5-5.5zM11.5 13.5 19 5" />
            </svg>
          </button>
        </form>
        <p className="composer-footnote">
          Answers use backend retrieval and self-evaluation. Conversation history is kept only in this session.
        </p>
      </div>

      {/* Toast notifications */}
      <div className="toast-container" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast--${t.type}`} role="alert">
            <svg aria-hidden="true" className="toast-icon" viewBox="0 0 24 24">
              {t.type === 'error'
                ? <><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></>
                : <path d="M20 6L9 17l-5-5" />}
            </svg>
            {t.message}
          </div>
        ))}
      </div>
    </section>
  )
}
