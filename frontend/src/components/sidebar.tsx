import type { ApiStatus, Page } from '../types'

interface SidebarProps {
  activePage: Page
  apiStatus: ApiStatus
  isOpen: boolean
  onNavigate: (page: Page) => void
}

export function Sidebar({
  activePage,
  apiStatus,
  isOpen,
  onNavigate,
}: SidebarProps) {
  return (
    <aside className={`sidebar${isOpen ? ' sidebar--open' : ''}`}>
      <div className="brand">
        <span aria-hidden="true" className="brand-mark">
          sr
        </span>
        <span>Self-RAG</span>
      </div>

      <nav aria-label="Main navigation" className="sidebar-actions">
        <button
          aria-current={activePage === 'chat' ? 'page' : undefined}
          className="nav-button"
          onClick={() => onNavigate('chat')}
          type="button"
        >
          <svg aria-hidden="true" className="nav-icon" viewBox="0 0 24 24">
            <path d="M12 5v14M5 12h14" />
          </svg>
          <span>New conversation</span>
        </button>
        <button
          aria-current={activePage === 'documents' ? 'page' : undefined}
          className="nav-button"
          onClick={() => onNavigate('documents')}
          type="button"
        >
          <svg aria-hidden="true" className="nav-icon" viewBox="0 0 24 24">
            <path d="M5 3.75h9l5 5v11.5H5z" />
            <path d="M14 3.75v5h5M8.5 13h7M8.5 16.5h7" />
          </svg>
          <span>Documents</span>
        </button>
      </nav>

      <div className="sidebar-caption">Workspace</div>

      <div className="sidebar-bottom">
        <div className="connection-state" aria-live="polite">
          <span className={`status-dot status-dot--${apiStatus}`} />
          <span>
            {apiStatus === 'checking'
              ? 'Checking API'
              : apiStatus === 'online'
                ? 'API connected'
                : 'API unavailable'}
          </span>
        </div>
      </div>
    </aside>
  )
}