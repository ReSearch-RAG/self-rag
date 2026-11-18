import { useCallback, useEffect, useRef, useState } from 'react'
import type { DragEvent, FormEvent } from 'react'
import { getDocuments, uploadDocument } from '../services/api'
import { useAuth } from '../context/AuthContext'
import type { Document } from '../types'

interface DocumentsPageProps {
  onSelectDocument: (document: Document) => void
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'An unexpected error occurred.'
}

export function DocumentsPage({ onSelectDocument }: DocumentsPageProps) {
  const { token } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const refreshDocuments = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setListError(null)
    try {
      setDocuments(await getDocuments(token))
    } catch (error) {
      setListError(getMessage(error))
    } finally {
      setIsLoading(false)
    }
  }, [token])

  useEffect(() => {
    void refreshDocuments()
  }, [refreshDocuments])

  // Drag-and-drop handlers
  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped && dropped.type === 'application/pdf') {
      setFile(dropped)
      setUploadError(null)
    } else {
      setUploadError('Only PDF files are accepted.')
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.currentTarget.files?.[0] ?? null
    setFile(selected)
    setUploadError(null)
  }

  async function handleUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setUploadError(null)
    setUploadMessage(null)

    if (!file) {
      setUploadError('Choose or drop a PDF file to upload.')
      return
    }

    if (!token) {
      setUploadError('Not authenticated.')
      return
    }

    setIsUploading(true)
    try {
      const uploaded = await uploadDocument(file, token)
      setUploadMessage(
        `${uploaded.filename} uploaded — status: ${uploaded.status}.`,
      )
      setFile(null)
      if (fileInput.current) fileInput.current.value = ''
      await refreshDocuments()
    } catch (error) {
      setUploadError(getMessage(error))
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <section aria-labelledby="documents-title" className="page-content">
      <div className="documents-page">
        {/* Heading */}
        <div className="documents-heading">
          <div className="empty-state-eyebrow">Your workspace</div>
          <h1 className="empty-state-title" id="documents-title">
            Documents
          </h1>
          <p className="empty-state-description">
            Upload a PDF and use processed documents for grounded chat.
            Processing status is reported by the backend.
          </p>
        </div>

        {/* Upload form */}
        <form className="upload-form" id="upload-form" onSubmit={(e) => void handleUpload(e)}>
          {/* Drag-and-drop zone */}
          <div
            className={`drop-zone${isDragging ? ' drop-zone--active' : ''}`}
            id="drop-zone"
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInput.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Drop PDF here or click to select"
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') fileInput.current?.click()
            }}
          >
            <svg
              aria-hidden="true"
              className="drop-zone-icon"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.4}
              viewBox="0 0 24 24"
            >
              <path d="M4 14.5V17a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-2.5" />
              <path d="M12 3v11M8 7l4-4 4 4" />
            </svg>
            {file ? (
              <span className="drop-zone-filename">{file.name}</span>
            ) : (
              <>
                <span>Drop a PDF here</span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>or click to browse</span>
              </>
            )}
          </div>

          {/* Hidden file input */}
          <input
            accept=".pdf,application/pdf"
            disabled={isUploading}
            id="document-file"
            onChange={handleFileChange}
            ref={fileInput}
            style={{ display: 'none' }}
            type="file"
          />

          {/* Upload progress */}
          {isUploading && (
            <div className="upload-progress" aria-label="Uploading…">
              <div className="upload-progress-bar" />
            </div>
          )}

          <button
            className="primary-button"
            disabled={isUploading || !file}
            id="upload-button"
            type="submit"
          >
            {isUploading ? (
              <>
                <span className="btn-spinner" style={{ borderTopColor: '#18140e', borderColor: 'rgba(24,20,14,0.3)' }} aria-hidden="true" />
                Uploading…
              </>
            ) : 'Upload PDF'}
          </button>

          {uploadError && (
            <p className="inline-error" role="alert">{uploadError}</p>
          )}
          {uploadMessage && (
            <p className="inline-message" role="status">{uploadMessage}</p>
          )}
        </form>

        {/* Document list */}
        <div className="document-list-heading">
          <h2>Uploaded documents</h2>
          <button
            className="text-button"
            disabled={isLoading}
            id="refresh-documents-button"
            onClick={() => void refreshDocuments()}
            type="button"
          >
            {isLoading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        {listError && (
          <p className="inline-error" role="alert">
            Could not load documents: {listError}
          </p>
        )}

        {isLoading && (
          <ul className="document-list" aria-label="Loading documents">
            {[1, 2, 3].map((n) => (
              <li key={n} className="skeleton skeleton-card" aria-hidden="true" />
            ))}
          </ul>
        )}

        {!isLoading && !listError && documents.length === 0 && (
          <p className="list-state">No documents have been uploaded yet.</p>
        )}

        {!isLoading && !listError && documents.length > 0 && (
          <ul aria-label="Uploaded documents" className="document-list">
            {documents.map((doc) => {
              const isProcessed = doc.status === 'processed'
              return (
                <li className="document-card" key={doc.id}>
                  <div className="document-card-main">
                    <span aria-hidden="true" className="document-file-mark">PDF</span>
                    <div className="document-card-copy">
                      <span className="document-name">{doc.filename}</span>
                      <span className="document-metadata">
                        Added {new Date(doc.created_at).toLocaleString()}
                        {' · '}ID {doc.id}
                      </span>
                    </div>
                  </div>
                  <div className="document-card-actions">
                    <span className={`document-status document-status--${doc.status}`}>
                      {doc.status}
                    </span>
                    <button
                      className="text-button"
                      disabled={!isProcessed}
                      id={`chat-about-${doc.id}`}
                      onClick={() => onSelectDocument(doc)}
                      type="button"
                    >
                      Chat about this
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </section>
  )
}
