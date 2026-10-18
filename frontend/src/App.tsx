import { useEffect, useState } from 'react'
import './App.css'
import { Header } from './components/header'
import { Sidebar } from './components/sidebar'
import { ChatPage } from './pages/chat'
import { DocumentsPage } from './pages/documents'
import { getHealth } from './services/api'
import type { ApiStatus, Document, Page } from './types'

function App() {
  const [page, setPage] = useState<Page>('chat')
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(
    null,
  )

  useEffect(() => {
    let active = true

    const checkHealth = async () => {
      try {
        const health = await getHealth()
        if (active) {
          setApiStatus(health.status === 'healthy' ? 'online' : 'offline')
        }
      } catch {
        if (active) setApiStatus('offline')
      }
    }

    void checkHealth()
    const intervalId = window.setInterval(checkHealth, 30_000)

    return () => {
      active = false
      window.clearInterval(intervalId)
    }
  }, [])

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
        {page === 'chat' ? (
          <ChatPage
            onBrowseDocuments={() => setPage('documents')}
            selectedDocument={selectedDocument}
          />
        ) : (
          <DocumentsPage
            onSelectDocument={(document) => {
              setSelectedDocument(document)
              setPage('chat')
            }}
          />
        )}
      </main>
    </div>
  )
}

export default App
