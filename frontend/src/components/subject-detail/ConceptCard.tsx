import type { ConceptWithMastery } from '@/types/concept'
import { Badge } from '@/components/ui/badge'

const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: 'text-green-400',
  intermediate: 'text-yellow-400',
  advanced: 'text-orange-400',
  expert: 'text-red-400',
}

const STATUS_COLORS: Record<string, string> = {
  mastered: 'bg-primary',
  learning: 'bg-secondary',
  reviewing: 'bg-secondary',
  not_started: 'bg-text-muted/30',
}

interface ConceptCardProps {
  readonly concept: ConceptWithMastery
}

export function ConceptCard({ concept }: ConceptCardProps) {
  const status = concept.mastery?.status ?? 'not_started'
  const level = concept.mastery?.mastery_level ?? 0

  return (
    <div className="rounded-lg border border-border bg-surface p-4 transition-colors hover:border-border/80">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h4 className="truncate font-body text-sm font-medium text-text-primary">
            {concept.name}
          </h4>
          <p className="mt-1 line-clamp-2 text-xs text-text-muted">{concept.description}</p>
        </div>
        <div className="text-right">
          <span className="font-mono text-xs text-text-muted">
            {status === 'not_started' ? '--' : `${Math.round(level * 100)}%`}
          </span>
        </div>
      </div>

      {/* Mastery bar (CSS-only) */}
      <div className="mt-3 h-1.5 w-full rounded-full bg-surface-elevated">
        <div
          className={`h-full rounded-full transition-[width] duration-300 ${STATUS_COLORS[status]}`}
          style={{ width: `${level * 100}%` }}
        />
      </div>

      {/* Metadata */}
      <div className="mt-2 flex items-center gap-2">
        <Badge variant="outline" className="font-mono text-[10px]">
          {concept.concept_type}
        </Badge>
        <span className={`font-mono text-[10px] ${DIFFICULTY_COLORS[concept.difficulty]}`}>
          {concept.difficulty}
        </span>
        <span className="font-mono text-[10px] text-text-muted">
          {concept.estimated_minutes} min
        </span>
      </div>
    </div>
  )
}
