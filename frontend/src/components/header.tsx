import type { ApiStatus, Page } from '../types'

interface HeaderProps {
  page: Page
  apiStatus: ApiStatus
  isMenuOpen: boolean
  onMenuClick: () => void
}

export function Header({
  page,
  apiStatus,
  isMenuOpen,
  onMenuClick,
}: HeaderProps) {
  return (
    <header className="page-header">
      <button
        aria-expanded={isMenuOpen}
        aria-label={isMenuOpen ? 'Close navigation' : 'Open navigation'}
        className="mobile-menu-button"
        onClick={onMenuClick}
        type="button"
      >
        <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>
      <div className="page-header-title">
        {page === 'chat' ? 'New conversation' : 'Documents'}
      </div>
      <div className="page-header-meta" aria-live="polite">
        {apiStatus === 'checking'
          ? 'Checking connection'
          : apiStatus === 'online'
            ? 'Connected'
            : 'Not connected'}
      </div>
    </header>
  )
}