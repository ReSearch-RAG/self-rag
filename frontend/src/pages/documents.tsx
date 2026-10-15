export function DocumentsPage() {
  return (
    <section aria-labelledby="documents-title" className="page-content">
      <div className="documents-empty-state">
        <div className="empty-state-eyebrow">Your workspace</div>
        <h1 className="empty-state-title" id="documents-title">
          Documents
        </h1>
        <p className="empty-state-description">
          Your documents will be listed here once document management is
          connected. No sample or placeholder files are being shown.
        </p>
        <div className="backend-note">
          <svg aria-hidden="true" className="header-icon" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 11v5M12 8h.01" />
          </svg>
          <span>
            Document listing and upload endpoints are not available in the
            backend yet.
          </span>
        </div>
      </div>
    </section>
  )
}