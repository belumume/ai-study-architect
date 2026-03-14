import { Outlet } from 'react-router-dom'
import { TopNav } from './TopNav'

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col bg-void text-text-primary">
      <TopNav />
      <main className="mx-auto w-full max-w-[1440px] flex-1 px-6 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-border py-4">
        <div className="mx-auto max-w-[1440px] px-6">
          <p className="font-mono text-xs text-text-muted">
            Study Architect by Quantelect
          </p>
        </div>
      </footer>
    </div>
  )
}
