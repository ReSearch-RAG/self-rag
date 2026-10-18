import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { getDocuments, uploadDocument } from '../services/api'
import type { Document } from '../types'

interface DocumentsPageProps {
  onSelectDocument: (document: Document) => void
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'An unexpected error occurred.'
}

export function DocumentsPage({ onSelectDocument }: DocumentsPageProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [userId, setUserId] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const refreshDocuments = useCallback(async () => {
    setIsLoading(true)
    setListError(null)

    try {
      setDocuments(await getDocuments())
    } catch (error) {
      setListError(getMessage(error))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true

    const loadDocuments = async () => {
      try {
        const nextDocuments = await getDocuments()
        if (active) {
          setDocuments(nextDocuments)
        }
      } catch (error) {
        if (active) {
          setListError(getMessage(error))
        }
      } finally {
        if (active) {
          setIsLoading(false)
        }
      }
    }

    void loadDocuments()
    return () => {
      active = false
    }
  }, [])

  const parsedUserId = Number(userId)
  const hasValidUserId =
    userId.trim().length > 0 &&
    Number.isInteger(parsedUserId) &&
    parsedUserId > 0

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setUploadError(null)
    setUploadMessage(null)

    if (!file) {
      setUploadError('Choose a PDF file to upload.')
      return
    }

    if (!hasValidUserId) {
      setUploadError('Enter a valid existing user ID.')
      return
    }

    setIsUploading(true)

    try {
      const uploadedDocument = await uploadDocument(file, parsedUserId)
      setUploadMessage(
        `${uploadedDocument.filename} upload finished with status: ${uploadedDocument.status}.`,
      )
      setFile(null)
      if (fileInput.current) {
        fileInput.current.value = ''
      }
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
        <div className="documents-heading">
          <div>
            <div className="empty-state-eyebrow">Your workspace</div>
            <h1 className="empty-state-title" id="documents-title">
              Documents
            </h1>
            <p className="empty-state-description">
              Upload a PDF and use processed documents for grounded chat.
              Processing status is reported by the backend.
            </p>
          </div>
        </div>

        <form className="upload-form" onSubmit={handleUpload}>
          <label className="form-label" htmlFor="document-file">
            PDF document
          </label>
          <input
            accept=".pdf,application/pdf"
            className="file-input"
            disabled={isUploading}
            id="document-file"
            onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
            ref={fileInput}
            type="file"
          />
          <label className="form-label" htmlFor="document-user-id">
            Existing user ID
          </label>
          <input
            className="text-input user-id-input"
            disabled={isUploading}
            id="document-user-id"
            min="1"
            onChange={(event) => setUserId(event.currentTarget.value)}
            placeholder="Required by the upload API"
            step="1"
            type="number"
            value={userId}
          />
          <button
            className="primary-button"
            disabled={isUploading || !file || !hasValidUserId}
            type="submit"
          >
            {isUploading ? 'Uploading and processing…' : 'Upload PDF'}
          </button>
          <p className="form-hint">
            Uploads are assigned to an existing backend user. The current API
            does not provide user registration or user lookup.
          </p>
          {uploadError && (
            <p className="inline-error" role="alert">
              {uploadError}
            </p>
          )}
          {uploadMessage && (
            <p className="inline-message" role="status">
              {uploadMessage}
            </p>
          )}
        </form>

        <div className="document-list-heading">
          <h2>Uploaded documents</h2>
          <button
            className="text-button"
            disabled={isLoading}
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
        {isLoading && <p className="list-state">Loading documents…</p>}
        {!isLoading && !listError && documents.length === 0 && (
          <p className="list-state">No documents have been uploaded yet.</p>
        )}
        {!isLoading && !listError && documents.length > 0 && (
          <ul aria-label="Uploaded documents" className="document-list">
            {documents.map((document) => {
              const isProcessed = document.status === 'processed'

              return (
                <li className="document-card" key={document.id}>
                  <div className="document-card-main">
                    <span aria-hidden="true" className="document-file-mark">
                      PDF
                    </span>
                    <div className="document-card-copy">
                      <span className="document-name">{document.filename}</span>
                      <span className="document-metadata">
                        Added {new Date(document.created_at).toLocaleString()}
                        {' · '}ID {document.id}
                      </span>
                    </div>
                  </div>
                  <div className="document-card-actions">
                    <span
                      className={`document-status document-status--${document.status}`}
                    >
                      {document.status}
                    </span>
                    <button
                      className="text-button"
                      disabled={!isProcessed}
                      onClick={() => onSelectDocument(document)}
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
