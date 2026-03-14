interface SubjectProgress {
  readonly id: string
  readonly name: string
  readonly color: string
  readonly weeklyGoalMinutes: number
  readonly weekMinutes: number
  readonly todayMinutes: number
}

interface SubjectListProps {
  readonly subjects: SubjectProgress[]
}

function formatHours(minutes: number): string {
  return (minutes / 60).toFixed(1)
}

export function SubjectList({ subjects }: SubjectListProps) {
  if (subjects.length === 0) return null

  return (
    <div className="space-y-2">
      <h2 className="font-display text-sm font-bold uppercase tracking-wider">Subject Mastery</h2>
      <div className="space-y-3">
        {subjects.map((subject) => {
          const progress =
            subject.weeklyGoalMinutes > 0
              ? Math.min(100, (subject.weekMinutes / subject.weeklyGoalMinutes) * 100)
              : 0

          return (
            <a
              href={`/subjects/${subject.id}`}
              key={subject.id}
              className="block rounded-lg border border-border bg-surface p-3 transition-colors hover:border-secondary/50"
            >
              <div className="flex items-center justify-between">
                <span className="font-body text-sm text-text-primary">{subject.name}</span>
                <span className="font-mono text-xs text-text-muted">
                  {formatHours(subject.weekMinutes)}/{formatHours(subject.weeklyGoalMinutes)}h
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-border">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${progress}%`,
                    backgroundColor: subject.color,
                    boxShadow: progress > 80 ? `0 0 10px ${subject.color}40` : undefined,
                  }}
                />
              </div>
            </a>
          )
        })}
      </div>
    </div>
  )
}
