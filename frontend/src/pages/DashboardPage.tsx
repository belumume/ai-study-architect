import { useAuth } from '@/contexts/AuthContext'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { BookOpen, Upload } from 'lucide-react'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold uppercase tracking-wider">
          Mission Control
        </h1>
        <p className="mt-1 font-body text-text-muted">
          Welcome back, {user?.full_name || user?.username}
        </p>
      </div>

      {/* Empty state — replaced by real dashboard in Phase 1.4 */}
      <Card className="border-border bg-surface p-8 text-center">
        <h3 className="font-display text-xl uppercase tracking-wider text-text-primary">
          Awaiting Telemetry
        </h3>
        <p className="mt-2 font-body text-text-muted">
          Create your first subject and start a focus session to begin tracking
        </p>
        <div className="mt-6 flex justify-center gap-4">
          <Button asChild className="bg-primary text-void hover:bg-primary/90">
            <Link to="/study">
              <BookOpen className="mr-2 h-4 w-4" />
              Start Study Session
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="border-border text-text-primary hover:bg-raised"
          >
            <Link to="/content">
              <Upload className="mr-2 h-4 w-4" />
              Upload Materials
            </Link>
          </Button>
        </div>
      </Card>
    </div>
  )
}
