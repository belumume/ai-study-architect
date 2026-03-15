import type { SubjectDetailData } from '@/types/concept'
import { MasteryRing } from './MasteryRing'

interface SubjectMasteryOverviewProps {
  readonly summary: SubjectDetailData['mastery_summary']
}

export function SubjectMasteryOverview({ summary }: SubjectMasteryOverviewProps) {
  const hasData = summary.total_concepts > 0

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-surface p-6">
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-primary/5 blur-2xl" />
      <div className="relative flex items-center gap-6">
        <div className="relative flex items-center justify-center">
          <MasteryRing percentage={hasData ? summary.mastery_percentage : 0} size={80} />
          <span className="absolute font-mono text-sm font-bold text-text-primary">
            {hasData ? `${Math.round(summary.mastery_percentage)}%` : '--'}
          </span>
        </div>
        <div className="space-y-1">
          <h3 className="font-display text-sm font-bold uppercase tracking-wider text-text-primary">
            Mastery Overview
          </h3>
          {hasData ? (
            summary.not_started_count === summary.total_concepts ? (
              <>
                <p className="font-mono text-xs text-text-muted">
                  {summary.total_concepts} concepts extracted
                </p>
                <p className="font-mono text-[10px] text-text-muted">
                  Practice features coming soon
                </p>
              </>
            ) : (
              <>
                <p className="font-mono text-xs text-text-muted">
                  {summary.mastered_count}/{summary.total_concepts} concepts mastered
                </p>
                <p className="font-mono text-[10px] text-text-muted">
                  {summary.learning_count} learning | {summary.not_started_count} not started
                </p>
              </>
            )
          ) : (
            <p className="font-mono text-xs text-text-muted">No concepts extracted yet</p>
          )}
        </div>
      </div>
    </div>
  )
}
