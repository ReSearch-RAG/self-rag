import { useEffect, useState } from 'react'
import './App.css'
import { AuthProvider, useAuth } from './context/AuthContext'
import { Header } from './components/header'
import { Sidebar } from './components/sidebar'
import { AuthPage } from './pages/auth'
import { ChatPage } from './pages/chat'
import { DashboardPage } from './pages/dashboard'
import { DocumentsPage } from './pages/documents'
import { getHealth } from './services/api'
import type { ApiStatus, Document, Page } from './types'

function AppShell() {
  const { isLoading, token } = useAuth()
  const [page, setPage] = useState<Page>('dashboard')
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)

  useEffect(() => {
    let active = true
    const checkHealth = async () => {
      try {
        const health = await getHealth()
        if (active) setApiStatus(health.status === 'healthy' ? 'online' : 'offline')
      } catch {
        if (active) setApiStatus('offline')
      }
    }
    void checkHealth()
    const id = window.setInterval(checkHealth, 30_000)
    return () => {
      active = false
      window.clearInterval(id)
    }
  }, [])

  // Show nothing while restoring session from localStorage
  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          color: 'var(--text-muted)',
          fontSize: 13,
          gap: 10,
        }}
      >
        <span
          style={{
            width: 18,
            height: 18,
            border: '2px solid var(--line-strong)',
            borderTopColor: 'var(--accent)',
            borderRadius: '50%',
            animation: 'spin 0.7s linear infinite',
            display: 'inline-block',
          }}
        />
        Loading…
      </div>
    )
  }

  // Not authenticated → show auth page
  if (!token) {
    return <AuthPage />
  }

  // Authenticated → show main app
  return (
    <div className="app-shell">
      <Sidebar
        activePage={page}
        apiStatus={apiStatus}
        isOpen={sidebarOpen}
        onNavigate={(nextPage) => {
          setPage(nextPage)
          setSidebarOpen(false)
        }}
      />
      <main className="main-panel">
        <Header
          page={page}
          apiStatus={apiStatus}
          isMenuOpen={sidebarOpen}
          onMenuClick={() => setSidebarOpen((open) => !open)}
        />

        {page === 'dashboard' && (
          <DashboardPage
            onNavigate={setPage}
            onSelectDocument={(doc) => {
              setSelectedDocument(doc)
            }}
          />
        )}

        {page === 'chat' && (
          <ChatPage
            onBrowseDocuments={() => setPage('documents')}
            selectedDocument={selectedDocument}
          />
        )}

        {page === 'documents' && (
          <DocumentsPage
            onSelectDocument={(doc) => {
              setSelectedDocument(doc)
              setPage('chat')
            }}
          />
        )}
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}

export default App
