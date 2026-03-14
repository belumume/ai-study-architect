import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import api from '@/services/api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { BookOpen, Upload, Loader2 } from 'lucide-react'
import {
  HeroMetrics,
  SubjectList,
  ContributionHeatmap,
  StartFocusCTA,
} from '@/components/dashboard'

interface DashboardData {
  today_minutes: number
  week_minutes: number
  current_streak: number
  active_session_id: string | null
  subjects: {
    id: string
    name: string
    color: string
    weekly_goal_minutes: number
    week_minutes: number
    today_minutes: number
  }[]
  heatmap: { date: string; minutes: number }[]
  mastery_index: number | null
  total_concepts: number
  mastered_concepts: number
}

export function DashboardPage() {
  const { user } = useAuth()

  const { data: dashboard, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/api/v1/dashboard/').then((r) => r.data),
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
    staleTime: 30_000,
  })

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  // Empty state (new user, no dashboard data yet or API not connected)
  if (!dashboard || (dashboard.subjects.length === 0 && dashboard.today_minutes === 0)) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-2xl font-bold uppercase tracking-wider">
            Mission Control
          </h1>
          <p className="mt-1 font-body text-text-muted">
            Welcome, {user?.full_name || user?.username}
          </p>
        </div>

        <HeroMetrics todayMinutes={0} streak={0} />

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

        <ContributionHeatmap
          data={
            dashboard?.heatmap ??
            Array.from({ length: 28 }, (_, i) => ({
              date: new Date(Date.now() - (27 - i) * 86400000).toISOString().split('T')[0],
              minutes: 0,
            }))
          }
        />
      </div>
    )
  }

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

      <HeroMetrics
        todayMinutes={dashboard.today_minutes}
        streak={dashboard.current_streak}
        masteryIndex={dashboard.mastery_index ?? undefined}
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="space-y-6">
          <SubjectList
            subjects={dashboard.subjects.map((s) => ({
              id: s.id,
              name: s.name,
              color: s.color,
              weeklyGoalMinutes: s.weekly_goal_minutes,
              weekMinutes: s.week_minutes,
              todayMinutes: s.today_minutes,
            }))}
          />
        </div>

        <div className="space-y-6">
          <ContributionHeatmap data={dashboard.heatmap} />
        </div>
      </div>

      <StartFocusCTA
        hasActiveSession={!!dashboard.active_session_id}
        activeSessionId={dashboard.active_session_id ?? undefined}
      />
    </div>
  )
}
