import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { User, LogOut } from 'lucide-react'

const NAV_LINKS = [
  { path: '/', label: 'Dashboard' },
  { path: '/study', label: 'Study' },
  { path: '/focus', label: 'Focus' },
  { path: '/content', label: 'Content' },
] as const

export function TopNav() {
  const { user, logout } = useAuth()
  const location = useLocation()

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-void/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1440px] items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link
            to="/"
            className="font-display text-lg font-bold uppercase tracking-wider text-primary"
          >
            Study Architect
          </Link>

          {user && (
            <nav className="flex items-center gap-1">
              {NAV_LINKS.map(({ path, label }) => (
                <Link
                  key={path}
                  to={path}
                  className={`px-3 py-1.5 font-body text-sm transition-colors ${
                    location.pathname === path
                      ? 'border-b-2 border-primary text-text-primary'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {label}
                </Link>
              ))}
            </nav>
          )}
        </div>

        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full text-text-muted hover:bg-raised hover:text-text-primary"
              >
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="border-border bg-surface text-text-primary">
              <DropdownMenuItem disabled className="text-text-muted">
                {user.username}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={logout}
                className="cursor-pointer text-tertiary focus:text-tertiary"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  )
}
