import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import api from '@/services/api'
import type { ExtractionResult } from '@/types/concept'

interface ExtractionTriggerProps {
  readonly contentId: string
  readonly subjectId: string
  readonly hasExistingConcepts: boolean
}

export function ExtractionTrigger({
  contentId,
  subjectId,
  hasExistingConcepts,
}: ExtractionTriggerProps) {
  const queryClient = useQueryClient()

  const mutation = useMutation<
    ExtractionResult,
    AxiosError<{ detail: string }>,
    { force_reextract?: boolean }
  >({
    mutationFn: (params) =>
      api
        .post('/api/v1/concepts/extract', {
          content_id: contentId,
          subject_id: subjectId,
          force_reextract: params?.force_reextract ?? false,
        })
        .then((r) => r.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subject-detail', subjectId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      const msg = data.chunks_failed
        ? `Extracted ${data.created_concepts} concepts from ${data.chunks_succeeded}/${data.chunks_total} sections.`
        : `Extracted ${data.created_concepts} concepts successfully.`
      toast.success(msg)
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail ?? 'Extraction failed. Please try again.')
    },
  })

  return (
    <Button
      size="sm"
      variant={hasExistingConcepts ? 'outline' : 'default'}
      disabled={mutation.isPending}
      onClick={() => mutation.mutate({ force_reextract: hasExistingConcepts })}
    >
      {mutation.isPending ? (
        <>
          <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />
          Extracting...
        </>
      ) : (
        <>
          <Sparkles className="mr-1.5 h-3 w-3" />
          {hasExistingConcepts ? 'Re-extract' : 'Extract Concepts'}
        </>
      )}
    </Button>
  )
}
