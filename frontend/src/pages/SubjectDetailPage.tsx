import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Link, Navigate, useParams } from 'react-router-dom'

import { ConceptCard } from '@/components/subject-detail/ConceptCard'
import { ExtractionTrigger } from '@/components/subject-detail/ExtractionTrigger'
import { SubjectMasteryOverview } from '@/components/subject-detail/SubjectMasteryOverview'
import api from '@/services/api'
import type { SubjectDetailData } from '@/types/concept'

export default function SubjectDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data, isLoading, error } = useQuery<SubjectDetailData>({
    queryKey: ['subject-detail', id],
    queryFn: () => api.get(`/api/v1/concepts/subjects/${id}/detail`).then((r) => r.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: !!id,
  })

  if (!id) return <Navigate to="/" replace />

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-text-muted" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4">
        <p className="font-body text-sm text-text-muted">Subject not found</p>
        <Link to="/" className="font-mono text-xs text-primary hover:underline">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/" className="text-text-muted transition-colors hover:text-text-primary">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: data.subject.color }} />
          <h1 className="font-display text-lg font-bold tracking-wide text-text-primary">
            {data.subject.name}
          </h1>
        </div>
      </div>

      {/* Mastery Overview */}
      <SubjectMasteryOverview summary={data.mastery_summary} />

      {/* Content Items */}
      {data.content_items.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-display text-sm font-bold uppercase tracking-wider text-text-muted">
            Content ({data.content_items.length})
          </h2>
          <div className="space-y-2">
            {data.content_items.map((content) => (
              <div
                key={content.id}
                className="flex items-center justify-between rounded-lg border border-border bg-surface p-3"
              >
                <div>
                  <p className="font-body text-sm text-text-primary">{content.title}</p>
                  <p className="font-mono text-[10px] text-text-muted">
                    {content.concept_count > 0
                      ? `${content.concept_count} concepts`
                      : content.extraction_status === 'extracting'
                        ? 'Extracting concepts...'
                        : content.extraction_status === 'completed_empty'
                          ? 'No concepts found -- try re-extracting'
                          : content.extraction_status === 'failed'
                            ? 'Extraction failed'
                            : content.processing_status === 'completed'
                              ? 'Ready to extract'
                              : content.processing_status}
                  </p>
                </div>
                {content.processing_status === 'completed' &&
                  content.extraction_status !== 'extracting' && (
                    <ExtractionTrigger
                      contentId={content.id}
                      subjectId={id}
                      hasExistingConcepts={content.concept_count > 0}
                    />
                  )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Concepts List */}
      <div className="space-y-3">
        <h2 className="font-display text-sm font-bold uppercase tracking-wider text-text-muted">
          Concepts ({data.mastery_summary.total_concepts})
        </h2>

        {data.concepts.length === 0 ? (
          <div className="rounded-xl border border-border/50 bg-surface p-8 text-center">
            <p className="font-body text-sm text-text-muted">
              {data.content_items.length === 0
                ? 'Upload study materials and link them to this subject to begin.'
                : 'Click "Extract Concepts" on a content item above to begin.'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {data.concepts.map((concept) => (
              <ConceptCard key={concept.id} concept={concept} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
