import { useRef, useState } from 'react'
import { sendChatMessage } from '../services/api'
import type { ChatMessage, Document } from '../types'

interface ChatPageProps {
  selectedDocument: Document | null
  onBrowseDocuments: () => void
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'An unexpected error occurred.'
}

export function ChatPage({
  selectedDocument,
  onBrowseDocuments,
}: ChatPageProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const requestInProgress = useRef(false)
  const nextMessageId = useRef(0)
  const canChat = selectedDocument?.status === 'processed'

  async function submitMessage() {
    const message = draft.trim()
    if (
      !message ||
      !selectedDocument ||
      !canChat ||
      requestInProgress.current
    ) {
      return
    }

    requestInProgress.current = true
    setDraft('')
    setError(null)
    setIsSending(true)
    setMessages((current) => [
      ...current,
      { id: ++nextMessageId.current, role: 'user', content: message },
    ])

    try {
      const response = await sendChatMessage(selectedDocument.id, message)
      setMessages((current) => [
        ...current,
        {
          id: ++nextMessageId.current,
          role: 'assistant',
          content: response.answer,
          isSufficient: response.is_sufficient,
          attempts: response.attempts,
        },
      ])
    } catch (requestError) {
      setError(getMessage(requestError))
    } finally {
      requestInProgress.current = false
      setIsSending(false)
    }
  }

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
              onClick={onBrowseDocuments}
              type="button"
            >
              Browse documents
            </button>
          )}
          {selectedDocument && !canChat && (
            <div className="backend-note">
              <svg
                aria-hidden="true"
                className="header-icon"
                viewBox="0 0 24 24"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M12 11v5M12 8h.01" />
              </svg>
              <span>
                {selectedDocument.filename} is {selectedDocument.status}.
                Chat is available only when the backend reports the document
                as processed.
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
              {message.role === 'assistant' && (
                <div
                  className={`answer-evidence answer-evidence--${message.isSufficient ? 'sufficient' : 'insufficient'}`}
                >
                  {message.isSufficient
                    ? 'Evidence evaluated as sufficient'
                    : 'Insufficient evidence — this is not a verified answer'}
                  {message.attempts !== undefined &&
                    ` · ${message.attempts} retrieval ${message.attempts === 1 ? 'attempt' : 'attempts'}`}
                </div>
              )}
            </article>
          ))}
          {isSending && (
            <p aria-live="polite" className="list-state">
              Retrieving evidence and preparing an answer…
            </p>
          )}
        </div>
      )}

      {error && (
        <p className="inline-error chat-error" role="alert">
          {error}
        </p>
      )}

      <div className="composer-area">
        {selectedDocument && (
          <p className="active-document">
            Document: <strong>{selectedDocument.filename}</strong>
          </p>
        )}
        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault()
            void submitMessage()
          }}
        >
          <textarea
            aria-label="Message"
            className="composer-input"
            disabled={!canChat || isSending}
            onChange={(event) => setDraft(event.currentTarget.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                void submitMessage()
              }
            }}
            placeholder={
              canChat ? 'Ask about this document…' : 'Select a processed document'
            }
            maxLength={4000}
            rows={1}
            value={draft}
          />
          <button
            aria-label="Send message"
            className="composer-action"
            disabled={!canChat || isSending || !draft.trim()}
            type="submit"
          >
            <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
              <path d="m5 12 14-7-4 14-3.5-5.5zM11.5 13.5 19 5" />
            </svg>
          </button>
        </form>
        <p className="composer-footnote">
          Answers use backend retrieval and evaluation. Conversation history is
          kept only in this page and is not persisted by the backend.
        </p>
      </div>
    </section>
  )
}
