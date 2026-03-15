export interface ConceptResponse {
  id: string
  content_id: string
  name: string
  description: string
  concept_type: 'definition' | 'procedure' | 'principle' | 'example' | 'application' | 'comparison'
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  estimated_minutes: number
  examples: string[] | null
  keywords: string[] | null
  extraction_confidence: number | null
  created_at: string
  updated_at: string
}

export interface MasteryData {
  id: string
  concept_id: string
  status: 'not_started' | 'learning' | 'reviewing' | 'mastered'
  mastery_level: number
  created_at: string
  updated_at: string
}

export interface ConceptWithMastery extends ConceptResponse {
  mastery: MasteryData | null
}

export interface ContentItem {
  id: string
  title: string
  content_type: string
  processing_status: string
  extraction_status: string | null
  concept_count: number
}

export interface SubjectDetailData {
  subject: { id: string; name: string; color: string }
  concepts: ConceptWithMastery[]
  content_items: ContentItem[]
  mastery_summary: {
    total_concepts: number
    mastered_count: number
    learning_count: number
    not_started_count: number
    mastery_percentage: number
    due_for_review: number
  }
}

export interface ExtractionResult {
  created_concepts: number
  created_dependencies: number
  chunks_total: number
  chunks_succeeded: number
  chunks_failed: number
  message: string | null
}
