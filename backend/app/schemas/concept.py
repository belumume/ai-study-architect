"""
Pydantic schemas for Knowledge Graph concepts and dependencies

These schemas support the mastery-based learning system for concept management.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.schemas.mastery import MasteryResponse


class ExternalResource(BaseModel):
    """Schema for external resource links with URL validation"""

    url: HttpUrl = Field(..., description="URL of the external resource")
    title: str = Field(..., min_length=1, max_length=255, description="Title of the resource")


# ============================================================================
# Concept Schemas
# ============================================================================


class ConceptBase(BaseModel):
    """Base concept schema with common attributes"""

    name: str = Field(..., min_length=1, max_length=255, description="Concept name")
    description: str = Field(
        ..., min_length=1, max_length=2000, description="Detailed concept description"
    )
    concept_type: str = Field(
        ...,
        description="Type of concept",
        pattern="^(definition|procedure|principle|example|application|comparison)$",
    )
    difficulty: str = Field(
        ..., description="Difficulty level", pattern="^(beginner|intermediate|advanced|expert)$"
    )
    estimated_minutes: int = Field(
        default=15, ge=0, le=480, description="Estimated time to master in minutes"
    )
    examples: list[str] | None = Field(
        default=None, description="List of example questions or scenarios"
    )
    keywords: list[str] | None = Field(default=None, description="Related keywords for search")
    external_resources: list[ExternalResource] | None = Field(
        default=None, description="Links to additional resources with validated URLs"
    )


class ConceptCreate(ConceptBase):
    """Schema for creating a new concept"""

    content_id: UUID = Field(..., description="ID of the content this concept was extracted from")
    subject_id: UUID | None = Field(
        default=None, description="ID of the subject this concept belongs to"
    )
    extraction_confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="AI extraction confidence score (0.0 to 1.0)"
    )
    extraction_metadata: dict[str, Any] | None = Field(
        default=None, description="Additional AI extraction metadata"
    )


class ConceptUpdate(BaseModel):
    """Schema for updating a concept"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    concept_type: str | None = Field(
        default=None, pattern="^(definition|procedure|principle|example|application|comparison)$"
    )
    difficulty: str | None = Field(
        default=None, pattern="^(beginner|intermediate|advanced|expert)$"
    )
    estimated_minutes: int | None = Field(default=None, ge=0, le=480)
    examples: list[str] | None = Field(default=None)
    keywords: list[str] | None = Field(default=None)
    external_resources: list[ExternalResource] | None = Field(default=None)

    model_config = ConfigDict(extra="forbid")


class ConceptResponse(ConceptBase):
    """Schema for concept response"""

    id: UUID
    content_id: UUID
    extraction_confidence: float | None = None
    extraction_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConceptDetail(ConceptResponse):
    """
    Detailed concept schema with relationships
    Includes prerequisite and dependent concepts
    """

    prerequisites: list["ConceptDependencyResponse"] = Field(
        default_factory=list, description="Concepts that are prerequisites for this one"
    )
    dependents: list["ConceptDependencyResponse"] = Field(
        default_factory=list, description="Concepts that depend on this one"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ConceptDependency Schemas
# ============================================================================


class ConceptDependencyBase(BaseModel):
    """Base concept dependency schema"""

    strength: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Dependency strength (0.0=optional, 1.0=required)"
    )
    reason: str | None = Field(
        default=None, max_length=500, description="Why this dependency exists"
    )


class ConceptDependencyCreate(ConceptDependencyBase):
    """Schema for creating a concept dependency"""

    prerequisite_concept_id: UUID = Field(
        ..., description="ID of the prerequisite concept (must be mastered first)"
    )
    dependent_concept_id: UUID = Field(
        ..., description="ID of the dependent concept (requires prerequisite)"
    )

    @field_validator("dependent_concept_id")
    @classmethod
    def validate_no_self_dependency(cls, v, info):
        """Prevent a concept from depending on itself"""
        if "prerequisite_concept_id" in info.data and v == info.data["prerequisite_concept_id"]:
            raise ValueError("A concept cannot depend on itself")
        return v


class ConceptDependencyResponse(ConceptDependencyBase):
    """Schema for concept dependency response"""

    id: UUID
    prerequisite_concept_id: UUID
    dependent_concept_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConceptDependencyDetail(ConceptDependencyResponse):
    """
    Detailed dependency schema with full concept information
    Useful for graph visualization
    """

    prerequisite_concept: ConceptResponse
    dependent_concept: ConceptResponse

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Knowledge Graph Schemas
# ============================================================================


class ConceptGraphNode(BaseModel):
    """Representation of a concept node in the knowledge graph"""

    id: UUID
    name: str
    difficulty: str
    concept_type: str
    estimated_minutes: int
    # Coordinates for graph visualization (can be calculated client-side)
    x: float | None = None
    y: float | None = None


class ConceptGraphEdge(BaseModel):
    """Representation of a dependency edge in the knowledge graph"""

    id: UUID
    source: UUID  # prerequisite_concept_id
    target: UUID  # dependent_concept_id
    strength: float


class ConceptGraph(BaseModel):
    """
    Full knowledge graph representation for a content item
    Optimized for graph visualization and traversal
    """

    content_id: UUID
    nodes: list[ConceptGraphNode] = Field(
        default_factory=list, description="All concepts as graph nodes"
    )
    edges: list[ConceptGraphEdge] = Field(
        default_factory=list, description="All dependencies as graph edges"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional graph metadata (total concepts, difficulty distribution, etc.)",
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# List Response Schemas
# ============================================================================


class ConceptListResponse(BaseModel):
    """Response for listing concepts with pagination"""

    items: list[ConceptResponse]
    total: int
    skip: int
    limit: int


class ConceptDependencyListResponse(BaseModel):
    """Response for listing concept dependencies"""

    items: list[ConceptDependencyResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# Bulk Operations Schemas
# ============================================================================


class ConceptBulkCreate(BaseModel):
    """Schema for bulk concept creation from knowledge graph extraction"""

    content_id: UUID
    concepts: list[ConceptCreate] = Field(
        ..., min_length=1, description="List of concepts to create"
    )
    dependencies: list[ConceptDependencyCreate] = Field(
        default_factory=list, description="List of dependencies between concepts"
    )
    extraction_metadata: dict[str, Any] | None = Field(
        default=None, description="Metadata about the extraction process"
    )


class ConceptBulkCreateResponse(BaseModel):
    """Response for bulk concept creation"""

    created_concepts: int
    created_dependencies: int
    concept_ids: list[UUID]
    dependency_ids: list[UUID]
    errors: list[str] = Field(default_factory=list, description="Any errors during creation")
    chunks_total: int = 0
    chunks_succeeded: int = 0
    chunks_failed: int = 0
    message: str | None = Field(
        default=None,
        description="User-facing message about the extraction result",
    )


# ============================================================================
# Extraction Schemas
# ============================================================================


class ConceptExtractionRequest(BaseModel):
    """Request to trigger concept extraction for a content item"""

    content_id: UUID
    subject_id: UUID
    force_reextract: bool = False


class ConceptWithMastery(ConceptResponse):
    """Concept with optional mastery data for the current user"""

    mastery: MasteryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Forward Reference Resolution
# ============================================================================
# Rebuild models to resolve forward references for circular dependencies
ConceptDetail.model_rebuild()
ConceptDependencyDetail.model_rebuild()
