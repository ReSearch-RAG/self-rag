import { useEffect, useState } from 'react'
import { getConversations, getDocuments } from '../services/api'
import { useAuth } from '../context/AuthContext'
import type { ConversationSummary, Document, Page } from '../types'

interface DashboardPageProps {
  onNavigate: (page: Page) => void
  onSelectDocument: (doc: Document) => void
}

export function DashboardPage({ onNavigate, onSelectDocument }: DashboardPageProps) {
  const { user, token } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!token) return
    let active = true

    Promise.all([getDocuments(token), getConversations(token)])
      .then(([docs, history]) => {
        if (!active) return
        setDocuments(docs)
        setConversations(history.conversations)
      })
      .catch(() => {
        if (!active) return
        getDocuments(token)
          .then((docs) => setDocuments(docs))
          .catch(() => undefined)
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [token])

  const firstName = user?.name?.split(' ')[0] ?? 'there'
  const processedCount = documents.filter((d) => d.status === 'processed').length
  const recentDocs = documents.slice(0, 5)

  return (
    <section aria-labelledby="dashboard-title" className="page-content">
      <div className="dashboard-page">
        {/* Greeting */}
        <div className="dashboard-greeting">
          <div className="empty-state-eyebrow">Overview</div>
          <h1 className="empty-state-title" id="dashboard-title">
            Hello, {firstName}.
          </h1>
          <p className="empty-state-description">
            Here's a snapshot of your Self-RAG workspace.
          </p>
        </div>

        {/* Stats */}
        <div className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-card-value">
              {isLoading ? '—' : documents.length}
            </div>
            <div className="stat-card-label">Total documents</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-value">
              {isLoading ? '—' : processedCount}
            </div>
            <div className="stat-card-label">Ready to chat</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-value">
              {isLoading ? '—' : documents.length - processedCount}
            </div>
            <div className="stat-card-label">Pending / failed</div>
          </div>
        </div>

        {/* Recent documents */}
        <h2 className="dashboard-section-title">Recent documents</h2>
        {isLoading && (
          <ul className="dashboard-recent-list" aria-label="Loading recent documents">
            {[1, 2, 3].map((n) => (
              <li key={n} className="skeleton" style={{ height: 52, borderRadius: 8 }} aria-hidden="true" />
            ))}
          </ul>
        )}
        {!isLoading && recentDocs.length === 0 && (
          <p className="list-state">No documents yet. Upload one to get started.</p>
        )}
        {!isLoading && recentDocs.length > 0 && (
          <ul className="dashboard-recent-list" aria-label="Recent documents">
            {recentDocs.map((doc) => (
              <li key={doc.id} className="dashboard-recent-item">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                  <span className="document-file-mark" aria-hidden="true" style={{ width: 30, height: 34, fontSize: 8 }}>PDF</span>
                  <div style={{ display: 'grid', gap: 3, minWidth: 0 }}>
                    <span className="document-name" style={{ fontSize: 13 }}>{doc.filename}</span>
                    <span className="document-metadata">{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                  <span className={`document-status document-status--${doc.status}`}>
                    {doc.status}
                  </span>
                  {doc.status === 'processed' && (
                    <button
                      className="text-button"
                      id={`dashboard-chat-${doc.id}`}
                      onClick={() => {
                        onSelectDocument(doc)
                        onNavigate('chat')
                      }}
                      type="button"
                    >
                      Chat
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        {/* Recent conversations */}
        <h2 className="dashboard-section-title">Recent conversations</h2>
        {isLoading && (
          <div className="dashboard-conversation-list" aria-label="Loading conversations">
            {[1, 2].map((n) => (
              <div key={n} className="skeleton" style={{ height: 74, borderRadius: 10 }} aria-hidden="true" />
            ))}
          </div>
        )}
        {!isLoading && conversations.length === 0 && (
          <p className="list-state">No conversations yet. Start by chatting with a document.</p>
        )}
        {!isLoading && conversations.length > 0 && (
          <div className="dashboard-conversation-list" aria-label="Recent conversations">
            {conversations.slice(0, 6).map((conversation) => {
              const document = documents.find((doc) => doc.id === conversation.document_id)
              return (
                <button
                  className="dashboard-conversation-card"
                  key={conversation.conversation_id}
                  onClick={() => {
                    if (document) {
                      onSelectDocument(document)
                      onNavigate('chat')
                    }
                  }}
                  type="button"
                >
                  <span className="conversation-icon" aria-hidden="true">
                    <svg className="header-icon" viewBox="0 0 24 24">
                      <path d="M4 5.5h16v11H9l-5 3z" />
                      <path d="M8 10h8M8 13.5h5" />
                    </svg>
                  </span>
                  <span className="conversation-main">
                    <span className="conversation-title">{conversation.document_name}</span>
                    <span className="conversation-preview">{conversation.preview}</span>
                  </span>
                  <span className="conversation-meta">
                    <span>{new Date(conversation.updated_at).toLocaleDateString()}</span>
                    <span>{conversation.message_count} messages</span>
                  </span>
                </button>
              )
            })}
          </div>
        )}

        {/* CTA */}
        <div className="dashboard-cta">
          <h2 className="dashboard-cta-title">Ready to start chatting?</h2>
          <p className="dashboard-cta-description">
            Upload a PDF and Self-RAG will retrieve and evaluate evidence to
            answer your questions — with self-correction built in.
          </p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button
              className="primary-button"
              id="dashboard-upload-cta"
              onClick={() => onNavigate('documents')}
              type="button"
            >
              <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
                <path d="M4 14.5V17a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-2.5" />
                <path d="M12 3v11M8 7l4-4 4 4" />
              </svg>
              Upload a document
            </button>
            {processedCount > 0 && (
              <button
                className="primary-button"
                id="dashboard-chat-cta"
                onClick={() => onNavigate('chat')}
                type="button"
                style={{ background: 'var(--surface-raised)', color: 'var(--accent)', borderColor: 'var(--line-accent)' }}
              >
                <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
                  <path d="M4 5.5h16v11H9l-5 3z" />
                </svg>
                Go to Chat
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
