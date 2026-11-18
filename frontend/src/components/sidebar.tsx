import { useAuth } from '../context/AuthContext'
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
  const { user, logout } = useAuth()

  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : '?'

  return (
    <aside className={`sidebar${isOpen ? ' sidebar--open' : ''}`}>
      {/* Brand */}
      <div className="brand">
        <span aria-hidden="true" className="brand-mark">sr</span>
        <span>Self-RAG</span>
      </div>

      {/* Nav */}
      <nav aria-label="Main navigation" className="sidebar-actions">
        <button
          aria-current={activePage === 'dashboard' ? 'page' : undefined}
          className="nav-button"
          id="nav-dashboard"
          onClick={() => onNavigate('dashboard')}
          type="button"
        >
          <svg aria-hidden="true" className="nav-icon" viewBox="0 0 24 24">
            <rect x="3" y="3" width="8" height="8" rx="1.5" />
            <rect x="13" y="3" width="8" height="8" rx="1.5" />
            <rect x="3" y="13" width="8" height="8" rx="1.5" />
            <rect x="13" y="13" width="8" height="8" rx="1.5" />
          </svg>
          <span>Dashboard</span>
        </button>

        <button
          aria-current={activePage === 'chat' ? 'page' : undefined}
          className="nav-button"
          id="nav-chat"
          onClick={() => onNavigate('chat')}
          type="button"
        >
          <svg aria-hidden="true" className="nav-icon" viewBox="0 0 24 24">
            <path d="M4 5.5h16v11H9l-5 3z" />
            <path d="M8 10h8M8 13.5h5" />
          </svg>
          <span>Chat</span>
        </button>

        <button
          aria-current={activePage === 'documents' ? 'page' : undefined}
          className="nav-button"
          id="nav-documents"
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

      {/* Bottom area */}
      <div className="sidebar-bottom">
        {/* User info */}
        {user && (
          <div className="sidebar-user">
            <span className="sidebar-user-avatar" aria-hidden="true">
              {initials}
            </span>
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{user.name}</span>
              <span className="sidebar-user-email">{user.email}</span>
            </div>
          </div>
        )}

        {/* Connection status */}
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

        {/* Logout */}
        <button
          className="logout-button"
          id="logout-button"
          onClick={logout}
          type="button"
        >
          <svg
            aria-hidden="true"
            className="nav-icon"
            viewBox="0 0 24 24"
          >
            <path d="M15 3H19a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H15" />
            <path d="M10 17l5-5-5-5M15 12H3" />
          </svg>
          Sign out
        </button>
      </div>
    </aside>
  )
}