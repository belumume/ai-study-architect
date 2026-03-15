"""
Concept extraction service — extracts atomic learning concepts from content text via Claude API.

Uses Claude Structured Outputs (output_config.format) for guaranteed valid JSON.
Parallel chunk processing with asyncio.Semaphore for throughput.
Prompt caching on system prompt for cost savings across chunks.
"""

import asyncio
import json
import logging
import os
import re
import uuid
from app.core.utils import utcnow

import httpx
from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.models.user_concept_mastery import UserConceptMastery
from app.schemas.concept import ConceptBase, ConceptBulkCreateResponse
from app.services.claude_service import claude_service
from app.services.content_processor import content_processor

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when ALL chunks fail. Partial success is a normal return."""

    pass


EXTRACTION_SYSTEM_PROMPT = """You are a concept extraction engine for an educational platform.
Extract atomic learning concepts from study material as Subject-Verb-Object (SVO) learning objectives.

GOOD concept names (specific, testable):
- "Calculate derivative using chain rule"
- "Implement binary search on sorted array"
- "Differentiate stack vs queue data structures"

BAD concept names (vague, untestable):
- "Understand calculus"
- "Binary search"
- "Data structures"

For each concept, provide:
- name: Clear SVO learning objective (3-10 words)
- description: Concise explanation (1-3 sentences)
- concept_type: definition | procedure | principle | example | application | comparison
- difficulty: beginner | intermediate | advanced | expert
- estimated_minutes: Time to master (5-60 minutes)
- keywords: 3-5 related search terms
- examples: 1-2 example questions testing this concept

Also identify prerequisite dependencies between extracted concepts:
- prerequisite_name: Name of the prerequisite concept
- dependent_name: Name of the concept that depends on it
- strength: 0.0 (loosely related) to 1.0 (absolutely required)
- reason: Brief explanation of why this dependency exists"""

CONCEPT_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "concept_type": {
                        "type": "string",
                        "enum": [
                            "definition",
                            "procedure",
                            "principle",
                            "example",
                            "application",
                            "comparison",
                        ],
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced", "expert"],
                    },
                    "estimated_minutes": {"type": "integer"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "examples": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "name",
                    "description",
                    "concept_type",
                    "difficulty",
                    "estimated_minutes",
                    "keywords",
                    "examples",
                ],
                "additionalProperties": False,
            },
        },
        "dependencies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "prerequisite_name": {"type": "string"},
                    "dependent_name": {"type": "string"},
                    "strength": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": [
                    "prerequisite_name",
                    "dependent_name",
                    "strength",
                    "reason",
                ],
                "additionalProperties": False,
            },
        },
        "metadata": {
            "type": "object",
            "properties": {
                "total_extracted": {"type": "integer"},
                "extraction_confidence": {"type": "number"},
                "notes": {"type": "string"},
            },
            "required": ["total_extracted", "extraction_confidence", "notes"],
            "additionalProperties": False,
        },
    },
    "required": ["concepts", "dependencies", "metadata"],
    "additionalProperties": False,
}


def normalize_concept_name(name: str) -> str:
    """Normalize concept name for deduplication."""
    normalized = name.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\b(the|a|an|of|in|on|for|to|and|vs|versus)\b", "", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


class ConceptExtractionService:
    """Extracts atomic learning concepts from content text via Claude API."""

    MAX_CHUNKS = 30
    MAX_CONCEPTS = 200
    MAX_TEXT_LENGTH = 100_000
    CHUNK_SIZE = 4000
    CHUNK_OVERLAP = 400

    async def extract_concepts(
        self,
        content_id: uuid.UUID,
        subject_id: uuid.UUID,
        extracted_text: str,
        user_id: uuid.UUID,
        db: Session,
    ) -> ConceptBulkCreateResponse:
        if not claude_service.api_key:
            raise ExtractionError("Claude API key not configured")

        text = extracted_text[: self.MAX_TEXT_LENGTH]

        chunks = content_processor.extract_chunks(text, self.CHUNK_SIZE, self.CHUNK_OVERLAP)
        chunks = chunks[: self.MAX_CHUNKS]

        if not chunks:
            raise ExtractionError("No text chunks to extract from")

        semaphore = asyncio.Semaphore(3)

        async def process_chunk(i: int, chunk: str) -> dict | None:
            async with semaphore:
                try:
                    return await self._call_claude(chunk, i + 1, len(chunks))
                except Exception as e:
                    logger.warning("Chunk %d/%d failed: %s", i + 1, len(chunks), e)
                    return None

        tasks = [process_chunk(i, chunk) for i, chunk in enumerate(chunks)]
        results = await asyncio.gather(*tasks)

        all_concepts = []
        all_dependencies = []
        seen_names: set[str] = set()
        chunks_succeeded = 0

        for result in results:
            if result is None:
                continue
            chunks_succeeded += 1

            validated = self._validate_concepts(result)
            for concept in validated.get("concepts", []):
                normalized = normalize_concept_name(concept["name"])
                if normalized not in seen_names:
                    all_concepts.append(concept)
                    seen_names.add(normalized)

            all_dependencies.extend(validated.get("dependencies", []))

        if chunks_succeeded == 0:
            raise ExtractionError(f"All {len(chunks)} chunks failed during extraction")

        all_concepts = all_concepts[: self.MAX_CONCEPTS]

        if not all_concepts:
            return ConceptBulkCreateResponse(
                created_concepts=0,
                created_dependencies=0,
                concept_ids=[],
                dependency_ids=[],
                errors=[],
                chunks_total=len(chunks),
                chunks_succeeded=chunks_succeeded,
                chunks_failed=len(chunks) - chunks_succeeded,
                message="No concepts found in this content. Try uploading more detailed study materials.",
            )

        concept_ids = self._bulk_insert(
            db, all_concepts, all_dependencies, content_id, subject_id, user_id
        )

        return ConceptBulkCreateResponse(
            created_concepts=len(concept_ids),
            created_dependencies=0,
            concept_ids=list(concept_ids.values()),
            dependency_ids=[],
            errors=[],
            chunks_total=len(chunks),
            chunks_succeeded=chunks_succeeded,
            chunks_failed=len(chunks) - chunks_succeeded,
        )

    async def _call_claude(self, chunk_text: str, chunk_num: int, total_chunks: int) -> dict:
        """Call Claude with Structured Outputs for guaranteed valid JSON."""
        model = os.getenv(
            "CLAUDE_EXTRACTION_MODEL",
            "claude-haiku-4-5",
        )
        payload = {
            "model": model,
            "max_tokens": 4096,
            "temperature": 0.15,
            "system": [
                {
                    "type": "text",
                    "text": EXTRACTION_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Extract concepts from this study material "
                        f"(section {chunk_num}/{total_chunks}):\n\n{chunk_text}"
                    ),
                }
            ],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": CONCEPT_EXTRACTION_SCHEMA,
                }
            },
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=5.0)) as client:
            response = await client.post(
                f"{claude_service.base_url}/messages",
                headers=claude_service._get_headers(),
                json=payload,
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", 5))
                logger.warning(
                    "Rate limited on chunk %d/%d, retrying in %ds",
                    chunk_num,
                    total_chunks,
                    retry_after,
                )
                await asyncio.sleep(retry_after)
                response = await client.post(
                    f"{claude_service.base_url}/messages",
                    headers=claude_service._get_headers(),
                    json=payload,
                )

            response.raise_for_status()
            data = response.json()

        return json.loads(data["content"][0]["text"])

    def _validate_concepts(self, parsed: dict) -> dict:
        """Validate extracted concepts through Pydantic schemas."""
        validated = []
        for c in parsed.get("concepts", []):
            try:
                ConceptBase(**c)
                validated.append(c)
            except Exception:
                logger.debug("Skipping invalid concept: %s", c.get("name", "?"))
                continue
        parsed["concepts"] = validated
        return parsed

    def _bulk_insert(
        self,
        db: Session,
        concepts_data: list[dict],
        dependencies_data: list[dict],  # noqa: ARG002 — reserved for Phase 2 iteration 2
        content_id: uuid.UUID,
        subject_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, uuid.UUID]:
        """Bulk insert concepts + mastery records using SQLAlchemy Core."""
        concept_records = [
            {
                "id": uuid.uuid4(),
                "name": c["name"],
                "description": c["description"],
                "concept_type": c.get("concept_type", "definition"),
                "difficulty": c.get("difficulty", "beginner"),
                "estimated_minutes": c.get("estimated_minutes", 15),
                "content_id": content_id,
                "subject_id": subject_id,
                "keywords": c.get("keywords"),
                "examples": c.get("examples"),
                "extraction_confidence": None,
                "created_at": utcnow(),
                "updated_at": utcnow(),
            }
            for c in concepts_data
        ]

        if concept_records:
            db.execute(insert(Concept), concept_records)

        concept_ids = {r["name"]: r["id"] for r in concept_records}

        mastery_records = [
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "concept_id": cid,
                "status": "not_started",
                "mastery_level": 0.0,
                "created_at": utcnow(),
                "updated_at": utcnow(),
            }
            for cid in concept_ids.values()
        ]

        if mastery_records:
            db.execute(insert(UserConceptMastery), mastery_records)

        db.flush()  # Ensure inserts are visible to subsequent queries in same transaction
        return concept_ids


concept_extraction_service = ConceptExtractionService()
