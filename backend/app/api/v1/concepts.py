"""
Concept extraction and subject detail endpoints.

Phase 2: POST /extract, GET /subjects/{id}/detail
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.rate_limiter import limiter
from app.models.concept import Concept
from app.models.content import Content
from app.models.subject import Subject
from app.models.user import User
from app.models.user_concept_mastery import UserConceptMastery
from app.schemas.concept import (
    ConceptBulkCreateResponse,
    ConceptExtractionRequest,
)
from app.services.concept_extraction import (
    ExtractionError,
    concept_extraction_service,
)

router = APIRouter(prefix="/concepts")


@router.post("/extract", response_model=ConceptBulkCreateResponse)
@limiter.limit("5/minute")
async def extract_concepts(
    request: Request,  # noqa: ARG001 — required by slowapi limiter
    extraction_request: ConceptExtractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger concept extraction for a content item."""
    content = (
        db.query(Content)
        .filter(
            Content.id == extraction_request.content_id,
            Content.user_id == current_user.id,
        )
        .first()
    )
    if not content:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Content not found")

    subject = (
        db.query(Subject)
        .filter(
            Subject.id == extraction_request.subject_id,
            Subject.user_id == current_user.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")

    if content.processing_status != "completed" or not content.extracted_text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Content text not yet extracted")

    rows = db.execute(
        update(Content)
        .where(
            Content.id == content.id,
            Content.extraction_status != "extracting",
        )
        .values(extraction_status="extracting")
    ).rowcount
    db.flush()
    if rows == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Extraction already in progress")

    if extraction_request.force_reextract:
        db.query(Concept).filter(Concept.content_id == content.id).delete()
        db.flush()

    try:
        result = await concept_extraction_service.extract_concepts(
            content.id,
            subject.id,
            content.extracted_text,
            current_user.id,
            db,
        )
        if result.chunks_failed:
            content.extraction_status = "partial"
        elif result.created_concepts == 0:
            content.extraction_status = "completed_empty"
        else:
            content.extraction_status = "completed"
        content.extraction_error = None
        # Update legacy key_concepts field with extracted concept names
        extracted = db.query(Concept.name).filter(Concept.content_id == content.id).all()
        content.key_concepts = [row.name for row in extracted]
        db.commit()
        return result
    except ExtractionError as e:
        content.extraction_status = "failed"
        content.extraction_error = str(e)[:500]
        db.commit()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Extraction failed: {e}") from e
    except Exception as e:
        # Catch unexpected exceptions to prevent extraction_status stuck as
        # "extracting" forever (which blocks all future extraction attempts)
        content.extraction_status = "failed"
        content.extraction_error = f"Unexpected: {e!s}"[:500]
        db.commit()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Extraction error") from e


@router.get("/subjects/{subject_id}/detail")
@limiter.limit("30/minute")
async def get_subject_detail(
    request: Request,  # noqa: ARG001 — required by slowapi limiter
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get subject with concepts and mastery summary (consolidated endpoint)."""
    subject = (
        db.query(Subject)
        .filter(
            Subject.id == subject_id,
            Subject.user_id == current_user.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")

    results = (
        db.query(Concept, UserConceptMastery)
        .outerjoin(
            UserConceptMastery,
            and_(
                UserConceptMastery.concept_id == Concept.id,
                UserConceptMastery.user_id == current_user.id,
            ),
        )
        .filter(Concept.subject_id == subject_id)
        .order_by(Concept.difficulty, Concept.name)
        .all()
    )

    concepts = []
    status_counts = {"not_started": 0, "learning": 0, "reviewing": 0, "mastered": 0}

    for concept, mastery in results:
        mastery_data = None
        if mastery:
            mastery_data = {
                "id": str(mastery.id),
                "concept_id": str(mastery.concept_id),
                "status": mastery.status,
                "mastery_level": mastery.mastery_level,
                "created_at": mastery.created_at.isoformat(),
                "updated_at": mastery.updated_at.isoformat(),
            }
            status_counts[mastery.status] = status_counts.get(mastery.status, 0) + 1
        else:
            status_counts["not_started"] += 1

        concepts.append(
            {
                "id": str(concept.id),
                "content_id": str(concept.content_id),
                "name": concept.name,
                "description": concept.description,
                "concept_type": concept.concept_type,
                "difficulty": concept.difficulty,
                "estimated_minutes": concept.estimated_minutes,
                "examples": concept.examples,
                "keywords": concept.keywords,
                "extraction_confidence": concept.extraction_confidence,
                "created_at": concept.created_at.isoformat(),
                "updated_at": concept.updated_at.isoformat(),
                "mastery": mastery_data,
            }
        )

    total = len(concepts)
    mastered = status_counts["mastered"]
    mastery_pct = (mastered / total * 100) if total > 0 else 0.0

    # Query content items linked to this subject
    content_items = (
        db.query(Content)
        .filter(
            Content.user_id == current_user.id,
            Content.subject_id == subject_id,
        )
        .order_by(Content.created_at.desc())
        .all()
    )

    content_list = [
        {
            "id": str(c.id),
            "title": c.title,
            "content_type": c.content_type,
            "processing_status": c.processing_status,
            "extraction_status": c.extraction_status,
            "concept_count": sum(1 for concept in concepts if concept["content_id"] == str(c.id)),
        }
        for c in content_items
    ]

    return {
        "subject": {
            "id": str(subject.id),
            "name": subject.name,
            "color": subject.color,
        },
        "concepts": concepts,
        "content_items": content_list,
        "mastery_summary": {
            "total_concepts": total,
            "mastered_count": mastered,
            "learning_count": status_counts["learning"],
            "not_started_count": status_counts["not_started"],
            "mastery_percentage": round(mastery_pct, 1),
            "due_for_review": 0,
        },
    }
