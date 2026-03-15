import { Card } from '@/components/ui/card'
import { Clock, Brain, Flame, AlertTriangle } from 'lucide-react'

interface HeroMetricsProps {
  readonly todayMinutes: number
  readonly masteryIndex?: number
  readonly totalConcepts?: number
  readonly streak: number
  readonly dueForReview?: number
}

function formatTime(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  const s = 0
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function HeroMetrics({
  todayMinutes,
  masteryIndex,
  totalConcepts,
  streak,
  dueForReview,
}: HeroMetricsProps) {
  const masteryValue = masteryIndex != null ? `${masteryIndex}%` : totalConcepts ? '0%' : '--'
  const masterySublabel =
    masteryIndex != null && masteryIndex > 0
      ? 'ACROSS SUBJECTS'
      : totalConcepts
        ? `${totalConcepts} CONCEPTS`
        : 'EXTRACT CONCEPTS FIRST'

  const metrics = [
    {
      label: "TODAY'S FOCUS",
      value: formatTime(todayMinutes),
      sublabel: 'DAILY TOTAL',
      icon: Clock,
      color: 'text-primary glow-primary',
      delay: '0ms',
    },
    {
      label: 'MASTERY INDEX',
      value: masteryValue,
      sublabel: masterySublabel,
      icon: Brain,
      color: 'text-secondary glow-secondary',
      delay: '200ms',
    },
    {
      label: 'CURRENT STREAK',
      value: `${streak}`,
      sublabel: streak === 1 ? 'DAY' : 'DAYS',
      icon: Flame,
      color: 'text-primary glow-primary',
      delay: '400ms',
    },
    {
      label: 'DUE FOR REVIEW',
      value: dueForReview != null ? `${dueForReview}` : '--',
      sublabel: 'CONCEPTS',
      icon: AlertTriangle,
      color:
        dueForReview && dueForReview > 0
          ? 'text-tertiary glow-tertiary'
          : 'text-secondary glow-secondary',
      delay: '600ms',
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {metrics.map((metric) => (
        <Card
          key={metric.label}
          className="relative overflow-hidden border-border bg-surface p-5"
          style={{
            animation: `fadeInUp 0.3s ease-out ${metric.delay} both`,
          }}
        >
          <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-primary/5 blur-2xl" />
          <p className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
            {metric.label}
          </p>
          <p className={`mt-1 font-mono text-3xl font-bold ${metric.color}`}>{metric.value}</p>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-text-muted">
            {metric.sublabel}
          </p>
        </Card>
      ))}
    </div>
  )
}
