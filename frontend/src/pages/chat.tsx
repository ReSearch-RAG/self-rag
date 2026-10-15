export function ChatPage() {
  return (
    <section aria-labelledby="chat-title" className="page-content">
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
          Start a conversation grounded in your own documents. Your workspace
          is ready; chat becomes available when its backend endpoint is in
          place.
        </p>
        <div className="backend-note">
          <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 11v5M12 8h.01" />
          </svg>
          <span>
            No conversation data is shown here. The backend currently provides
            a health check only.
          </span>
        </div>
      </div>

      <div className="composer-area">
        <div className="composer">
          <textarea
            aria-label="Message"
            className="composer-input"
            disabled
            placeholder="Chat is not available yet"
            rows={1}
          />
          <button
            aria-label="Send message"
            className="composer-action"
            disabled
            type="button"
          >
            <svg className="header-icon" viewBox="0 0 24 24">
              <path d="m5 12 14-7-4 14-3.5-5.5zM11.5 13.5 19 5" />
            </svg>
          </button>
        </div>
        <p className="composer-footnote">
          No messages will be sent until a chat endpoint is connected.
        </p>
      </div>
    </section>
  )
}