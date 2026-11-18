import { useAuth } from '../context/AuthContext'
import type { ApiStatus, Page } from '../types'

const PAGE_TITLES: Record<Page, string> = {
  dashboard: 'Dashboard',
  chat: 'Chat',
  documents: 'Documents',
}

interface HeaderProps {
  page: Page
  apiStatus: ApiStatus
  isMenuOpen: boolean
  onMenuClick: () => void
}

export function Header({ page, apiStatus, isMenuOpen, onMenuClick }: HeaderProps) {
  const { user } = useAuth()

  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : '?'

  const statusLabel =
    apiStatus === 'checking'
      ? 'Checking connection'
      : apiStatus === 'online'
        ? 'Connected'
        : 'Not connected'

  return (
    <header className="page-header">
      <div className="page-header-left">
        <button
          aria-expanded={isMenuOpen}
          aria-label={isMenuOpen ? 'Close navigation' : 'Open navigation'}
          className="mobile-menu-button"
          id="mobile-menu-button"
          onClick={onMenuClick}
          type="button"
        >
          <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>
        <div className="page-header-title">{PAGE_TITLES[page]}</div>
      </div>

      <div className="page-header-right">
        <div className="page-header-status" aria-live="polite" aria-label="API status">
          <span className={`status-dot status-dot--${apiStatus}`} />
          <span>{statusLabel}</span>
        </div>
        {user && (
          <div
            className="header-user-badge"
            aria-label={`Signed in as ${user.name}`}
            title={user.name}
          >
            {initials}
          </div>
        )}
      </div>
    </header>
  )
}