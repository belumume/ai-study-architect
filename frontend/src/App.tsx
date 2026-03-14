import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider } from './contexts/AuthContext'
import { GuestRoute, ProtectedRoute } from './components/auth'
import { LoginForm, RegisterForm } from './components/auth'
import { AppShell } from './app/layout'
import { DashboardPage, StudyPage, ContentPage, FocusPage } from './pages'
import SubjectDetailPage from './pages/SubjectDetailPage'
import { ErrorBoundary } from './components/ErrorBoundary'
import api from './services/api'
import tokenStorage from './services/tokenStorage'

function App() {
  useEffect(() => {
    tokenStorage.migrateFromLocalStorage()
  }, [])

  useEffect(() => {
    api.get('/api/v1/csrf/token').catch(() => {})
  }, [])

  return (
    <ErrorBoundary>
      <AuthProvider>
        <Routes>
          {/* Auth routes (no shell) */}
          <Route
            path="/login"
            element={
              <GuestRoute>
                <div className="flex min-h-screen items-center justify-center bg-void">
                  <LoginForm />
                </div>
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <div className="flex min-h-screen items-center justify-center bg-void">
                  <RegisterForm />
                </div>
              </GuestRoute>
            }
          />

          {/* App routes (with shell) */}
          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/subjects/:id" element={<SubjectDetailPage />} />
            <Route path="/study" element={<StudyPage />} />
            <Route path="/focus" element={<FocusPage />} />
            <Route path="/content" element={<ContentPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
