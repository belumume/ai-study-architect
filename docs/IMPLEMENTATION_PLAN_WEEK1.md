# Week 1 Implementation Plan: Knowledge Graph Extraction

**Goal**: Extract atomic concepts and dependencies from CS50 course materials using Claude AI

**Timeframe**: 7-10 days
**Prerequisites**: Current backend infrastructure (FastAPI, Claude service, database)

---

## Overview

We're building the foundation of the mastery-based learning system: automatic extraction of knowledge graphs from course materials.

**Input**: CS50 lecture notes, problem sets, documentation
**Output**: Directed acyclic graph (DAG) of concepts with dependencies

**Example**:
```
CS50 Week 1 → Extract → {
  "Variables": {id: 1, difficulty: "beginner", prerequisites: []},
  "Data Types": {id: 2, difficulty: "beginner", prerequisites: [1]},
  "Operators": {id: 3, difficulty: "beginner", prerequisites: [1, 2]},
  "Conditionals": {id: 4, difficulty: "intermediate", prerequisites: [3]},
  ...
}
```

---

## Day 1-2: Database Schema & Models

### Task 1.1: Create Database Tables

```sql
-- File: backend/alembic/versions/xxx_add_knowledge_graph_tables.py

"""add knowledge graph tables

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Create ENUMs for data integrity
    difficulty_enum = sa.Enum('beginner', 'intermediate', 'advanced', name='difficulty_level')
    strength_enum = sa.Enum('required', 'recommended', 'optional', name='dependency_strength')

    difficulty_enum.create(op.get_bind())
    strength_enum.create(op.get_bind())

    # Concepts table
    op.create_table(
        'concepts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('course_id', UUID(as_uuid=True), sa.ForeignKey('content.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),  # URL-friendly name
        sa.Column('description', sa.Text),
        sa.Column('difficulty', difficulty_enum, nullable=False, server_default='beginner'),
        sa.Column('estimated_hours', sa.Float),  # Time to master
        sa.Column('example_code', sa.Text),  # Optional example
        sa.Column('keywords', JSONB),  # For search
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        # Constraints for data integrity
        sa.UniqueConstraint('course_id', 'slug', name='unique_concept_slug_per_course'),
        sa.CheckConstraint('estimated_hours > 0', name='positive_estimated_hours')
    )

    # Concept dependencies table
    op.create_table(
        'concept_dependencies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('concept_id', UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prerequisite_id', UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strength', strength_enum, nullable=False, server_default='required'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        # Prevent duplicate dependencies
        sa.UniqueConstraint('concept_id', 'prerequisite_id', name='unique_dependency'),
        # Prevent self-dependencies
        sa.CheckConstraint('concept_id != prerequisite_id', name='no_self_dependency')
    )

    # Create indexes for performance
    op.create_index('idx_concepts_course_id', 'concepts', ['course_id'])
    op.create_index('idx_concepts_difficulty', 'concepts', ['difficulty'])
    op.create_index('idx_concepts_slug', 'concepts', ['slug'])
    op.create_index('idx_concept_deps_concept', 'concept_dependencies', ['concept_id'])
    op.create_index('idx_concept_deps_prereq', 'concept_dependencies', ['prerequisite_id'])

def downgrade():
    # Drop tables
    op.drop_table('concept_dependencies')
    op.drop_table('concepts')

    # Drop ENUMs
    sa.Enum(name='dependency_strength').drop(op.get_bind())
    sa.Enum(name='difficulty_level').drop(op.get_bind())
```

### Task 1.2: Create SQLAlchemy Models

```python
# File: backend/app/models/concept.py

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, UniqueConstraint, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class DifficultyLevel(str, enum.Enum):
    """Enum for concept difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DependencyStrength(str, enum.Enum):
    """Enum for prerequisite dependency strength"""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class Concept(Base):
    """
    Represents an atomic learning concept extracted from course materials.
    Examples: "for loops", "arrays", "pointers", "recursion"
    """
    __tablename__ = "concepts"
    __table_args__ = (
        UniqueConstraint('course_id', 'slug', name='unique_concept_slug_per_course'),
        CheckConstraint('estimated_hours > 0', name='positive_estimated_hours'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text)
    difficulty = Column(Enum(DifficultyLevel), nullable=False, server_default=DifficultyLevel.BEGINNER.value)
    estimated_hours = Column(Float)
    example_code = Column(Text)
    keywords = Column(JSONB)  # ["loop", "iteration", "for", "while"]
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Content", back_populates="concepts")
    prerequisites = relationship(
        "Concept",
        secondary="concept_dependencies",
        primaryjoin="Concept.id==ConceptDependency.concept_id",
        secondaryjoin="Concept.id==ConceptDependency.prerequisite_id",
        backref="dependent_concepts"
    )

    def __repr__(self):
        return f"<Concept {self.name} (difficulty={self.difficulty.value})>"


class ConceptDependency(Base):
    """
    Represents prerequisite relationships between concepts.
    Example: "arrays" requires "loops" and "variables"
    """
    __tablename__ = "concept_dependencies"
    __table_args__ = (
        UniqueConstraint('concept_id', 'prerequisite_id', name='unique_dependency'),
        CheckConstraint('concept_id != prerequisite_id', name='no_self_dependency'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    prerequisite_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    strength = Column(Enum(DependencyStrength), nullable=False, server_default=DependencyStrength.REQUIRED.value)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Dependency {self.concept_id} requires {self.prerequisite_id} ({self.strength.value})>"
```

### Task 1.3: Create Pydantic Schemas

```python
# File: backend/app/schemas/concept.py

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class ConceptBase(BaseModel):
    name: str = Field(..., description="Concept name, e.g., 'for loops'")
    description: Optional[str] = Field(None, description="Detailed explanation")
    difficulty: str = Field("beginner", description="beginner, intermediate, or advanced")
    estimated_hours: Optional[float] = Field(None, description="Time to master in hours")
    example_code: Optional[str] = Field(None, description="Code example")
    keywords: Optional[List[str]] = Field(default_factory=list)

class ConceptCreate(ConceptBase):
    course_id: UUID
    slug: str

class ConceptResponse(ConceptBase):
    id: UUID
    course_id: UUID
    slug: str
    created_at: datetime
    prerequisite_ids: List[UUID] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ConceptGraph(BaseModel):
    """Complete knowledge graph for a course"""
    concepts: List[ConceptResponse]
    dependencies: List[dict]  # [{from: uuid, to: uuid, strength: str}]

    class Config:
        from_attributes = True
```

**Deliverable**: Run migration, create tables, test CRUD operations

---

## Day 3-4: Knowledge Graph Extraction Service

### Task 2.1: Create Extraction Prompts

```python
# File: backend/app/prompts/knowledge_graph_extraction.py

EXTRACT_CONCEPTS_PROMPT = """You are an expert at analyzing educational materials and extracting atomic learning concepts.

Given the following course material, extract all distinct concepts that a student needs to learn.

COURSE MATERIAL:
{material_text}

For each concept, provide:
1. **Name**: Short, clear name (2-5 words)
2. **Description**: What the student needs to understand (1-2 sentences)
3. **Difficulty**: beginner, intermediate, or advanced
4. **Estimated Hours**: Realistic time to master (0.5 - 10 hours)
5. **Keywords**: Related terms for searching
6. **Example**: Brief code example or explanation

OUTPUT FORMAT (JSON):
```json
{{
  "concepts": [
    {{
      "name": "Variables",
      "slug": "variables",
      "description": "Understanding how to declare and use variables to store data",
      "difficulty": "beginner",
      "estimated_hours": 1.0,
      "keywords": ["var", "declaration", "assignment", "data storage"],
      "example_code": "int x = 5;\\nstring name = \\"Alice\\";"
    }},
    ...
  ]
}}
```

RULES:
- Concepts should be atomic (teach one thing well)
- Names should be consistent with standard terminology
- Difficulty should match a beginner programmer's perspective
- Be comprehensive but avoid redundancy
"""

EXTRACT_DEPENDENCIES_PROMPT = """You are an expert at understanding prerequisite relationships in learning.

Given these concepts from a course, identify which concepts are prerequisites for others.

CONCEPTS:
{concepts_json}

For each concept, identify:
1. What must be understood BEFORE learning this concept (required prerequisites)
2. What would be helpful but not strictly necessary (recommended)

OUTPUT FORMAT (JSON):
```json
{{
  "dependencies": [
    {{
      "concept": "Arrays",
      "prerequisite": "Variables",
      "strength": "required",
      "reason": "Must understand variables before using arrays"
    }},
    {{
      "concept": "Loops",
      "prerequisite": "Conditionals",
      "strength": "recommended",
      "reason": "Conditionals help understand loop control flow"
    }},
    ...
  ]
}}
```

RULES:
- Only include TRUE dependencies (not just "helpful to know")
- Avoid circular dependencies
- A concept can have 0-5 prerequisites (keep it simple)
- Strength: "required" or "recommended"
"""
```

### Task 2.2: Implement Knowledge Graph Service

```python
# File: backend/app/services/knowledge_graph_service.py

import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.concept import Concept, ConceptDependency
from app.models.content import Content
from app.services.claude_service import ClaudeService
from app.prompts.knowledge_graph_extraction import (
    EXTRACT_CONCEPTS_PROMPT,
    EXTRACT_DEPENDENCIES_PROMPT
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for extracting and managing knowledge graphs from course materials"""

    def __init__(self, db: Session):
        self.db = db
        self.claude = ClaudeService()

    async def extract_knowledge_graph(
        self,
        course_id: UUID,
        force_reextract: bool = False
    ) -> Dict[str, Any]:
        """
        Extract complete knowledge graph from course materials.

        Args:
            course_id: ID of the content/course to process
            force_reextract: If True, delete existing concepts and re-extract

        Returns:
            {
                "concepts": [...],
                "dependencies": [...],
                "stats": {concept_count, dependency_count}
            }
        """
        # Get course content
        course = self.db.query(Content).filter(Content.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found")

        # Check if already extracted
        existing_concepts = self.db.query(Concept).filter(
            Concept.course_id == course_id
        ).count()

        if existing_concepts > 0 and not force_reextract:
            logger.info(f"Course {course_id} already has {existing_concepts} concepts")
            return self.get_knowledge_graph(course_id)

        if force_reextract:
            logger.info(f"Force re-extracting concepts for course {course_id}")
            self._delete_existing_concepts(course_id)

        # Step 1: Extract concepts
        logger.info(f"Extracting concepts from course {course_id}")
        concepts = await self._extract_concepts(course)

        # Step 2: Save concepts to database
        concept_map = {}  # name -> Concept object
        for concept_data in concepts:
            concept = Concept(
                course_id=course_id,
                name=concept_data["name"],
                slug=concept_data["slug"],
                description=concept_data.get("description"),
                difficulty=concept_data.get("difficulty", "beginner"),
                estimated_hours=concept_data.get("estimated_hours"),
                example_code=concept_data.get("example_code"),
                keywords=concept_data.get("keywords", [])
            )
            self.db.add(concept)
            self.db.flush()  # Get ID without committing
            concept_map[concept.name] = concept

        self.db.commit()
        logger.info(f"Saved {len(concepts)} concepts")

        # Step 3: Extract dependencies
        logger.info("Extracting concept dependencies")
        dependencies = await self._extract_dependencies(concepts)

        # Step 4: Save dependencies
        dep_count = 0
        for dep_data in dependencies:
            concept_name = dep_data["concept"]
            prereq_name = dep_data["prerequisite"]

            if concept_name not in concept_map or prereq_name not in concept_map:
                logger.warning(f"Skipping invalid dependency: {prereq_name} -> {concept_name}")
                continue

            dependency = ConceptDependency(
                concept_id=concept_map[concept_name].id,
                prerequisite_id=concept_map[prereq_name].id,
                strength=dep_data.get("strength", "required")
            )
            self.db.add(dependency)
            dep_count += 1

        self.db.commit()
        logger.info(f"Saved {dep_count} dependencies")

        # Return the extracted graph
        return {
            "concepts": [self._concept_to_dict(c) for c in concept_map.values()],
            "dependencies": dependencies,
            "stats": {
                "concept_count": len(concepts),
                "dependency_count": dep_count
            }
        }

    async def _extract_concepts(self, course: Content) -> List[Dict[str, Any]]:
        """Use Claude to extract concepts from course material"""
        prompt = EXTRACT_CONCEPTS_PROMPT.format(
            material_text=course.extracted_text[:10000]  # First 10k chars
        )

        response = await self.claude.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for structured extraction
            max_tokens=4000
        )

        # Parse JSON response
        try:
            result = json.loads(response["response"])
            concepts = result.get("concepts", [])

            # Generate slugs
            for concept in concepts:
                if "slug" not in concept:
                    concept["slug"] = concept["name"].lower().replace(" ", "-")

            return concepts
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse concept extraction: {e}")
            logger.error(f"Response was: {response}")
            return []

    async def _extract_dependencies(
        self,
        concepts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use Claude to identify prerequisite relationships"""
        concepts_json = json.dumps(
            [{"name": c["name"], "description": c.get("description", "")} for c in concepts],
            indent=2
        )

        prompt = EXTRACT_DEPENDENCIES_PROMPT.format(
            concepts_json=concepts_json
        )

        response = await self.claude.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000
        )

        try:
            result = json.loads(response["response"])
            return result.get("dependencies", [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse dependency extraction: {e}")
            return []

    def get_knowledge_graph(self, course_id: UUID) -> Dict[str, Any]:
        """Retrieve existing knowledge graph from database"""
        concepts = self.db.query(Concept).filter(
            Concept.course_id == course_id
        ).all()

        dependencies = self.db.query(ConceptDependency).join(
            Concept, ConceptDependency.concept_id == Concept.id
        ).filter(Concept.course_id == course_id).all()

        return {
            "concepts": [self._concept_to_dict(c) for c in concepts],
            "dependencies": [
                {
                    "from": str(d.prerequisite_id),
                    "to": str(d.concept_id),
                    "strength": d.strength
                }
                for d in dependencies
            ],
            "stats": {
                "concept_count": len(concepts),
                "dependency_count": len(dependencies)
            }
        }

    def _concept_to_dict(self, concept: Concept) -> Dict[str, Any]:
        """Convert Concept model to dictionary"""
        return {
            "id": str(concept.id),
            "name": concept.name,
            "slug": concept.slug,
            "description": concept.description,
            "difficulty": concept.difficulty,
            "estimated_hours": concept.estimated_hours,
            "example_code": concept.example_code,
            "keywords": concept.keywords or []
        }

    def _delete_existing_concepts(self, course_id: UUID):
        """Delete all concepts and dependencies for a course"""
        # Dependencies will cascade delete
        self.db.query(Concept).filter(Concept.course_id == course_id).delete()
        self.db.commit()
```

**Deliverable**: Service that extracts concepts from text

---

## Day 5-6: API Endpoints

### Task 3.1: Create Knowledge Graph Endpoints

```python
# File: backend/app/api/v1/knowledge_graph.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.post("/extract/{course_id}", response_model=Dict[str, Any])
async def extract_knowledge_graph(
    course_id: UUID,
    force_reextract: bool = False,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract knowledge graph from course materials.

    This process:
    1. Uses Claude to analyze course content
    2. Extracts atomic concepts
    3. Identifies prerequisite relationships
    4. Stores as graph in database

    Can take 30-60 seconds for large courses.
    """
    service = KnowledgeGraphService(db)

    try:
        # Run extraction
        result = await service.extract_knowledge_graph(
            course_id=course_id,
            force_reextract=force_reextract
        )

        return {
            "success": True,
            "message": f"Extracted {result['stats']['concept_count']} concepts",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract knowledge graph: {str(e)}"
        )


@router.get("/{course_id}", response_model=Dict[str, Any])
async def get_knowledge_graph(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the knowledge graph for a course.

    Returns concepts and their prerequisite relationships
    for visualization and navigation.
    """
    service = KnowledgeGraphService(db)

    result = service.get_knowledge_graph(course_id)

    if result["stats"]["concept_count"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No knowledge graph found. Extract it first with POST /knowledge-graph/extract/{course_id}"
        )

    return {
        "success": True,
        "data": result
    }


@router.get("/concepts/{concept_id}", response_model=Dict[str, Any])
async def get_concept_details(
    concept_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific concept"""
    from app.models.concept import Concept

    concept = db.query(Concept).filter(Concept.id == concept_id).first()

    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept {concept_id} not found"
        )

    # Get prerequisites
    prerequisites = [
        {
            "id": str(p.id),
            "name": p.name,
            "difficulty": p.difficulty
        }
        for p in concept.prerequisites
    ]

    # Get dependent concepts (what unlocks after this)
    dependents = [
        {
            "id": str(d.id),
            "name": d.name,
            "difficulty": d.difficulty
        }
        for d in concept.dependent_concepts
    ]

    return {
        "success": True,
        "data": {
            "concept": {
                "id": str(concept.id),
                "name": concept.name,
                "description": concept.description,
                "difficulty": concept.difficulty,
                "estimated_hours": concept.estimated_hours,
                "example_code": concept.example_code,
                "keywords": concept.keywords
            },
            "prerequisites": prerequisites,
            "unlocks": dependents
        }
    }
```

### Task 3.2: Register Routes

```python
# File: backend/app/api/v1/api.py

from fastapi import APIRouter
from app.api.v1 import (
    auth,
    content,
    chat,
    agents,
    knowledge_graph,  # NEW
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(knowledge_graph.router, prefix="/knowledge-graph", tags=["knowledge-graph"])  # NEW
```

**Deliverable**: Working API endpoints to extract and retrieve graphs

---

## Day 7: Testing with Real CS50 Materials

### Task 4.1: Get CS50 Materials

Download CS50 Week 1-3 materials:
- Lecture notes
- Problem set descriptions
- Example code

Save to `backend/tests/fixtures/cs50_week1.txt`

### Task 4.2: Create Test Script

```python
# File: backend/tests/scripts/test_knowledge_graph_extraction.py

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.models.content import Content
from app.services.knowledge_graph_service import KnowledgeGraphService


async def test_extraction():
    """Test knowledge graph extraction with CS50 materials"""

    # Read test fixture
    fixture_path = Path(__file__).parent.parent / "fixtures" / "cs50_week1.txt"
    with open(fixture_path, "r") as f:
        material_text = f.read()

    # Create test content
    db = SessionLocal()

    content = Content(
        user_id="test-user-id",  # Replace with actual test user
        title="CS50 Week 1",
        file_type="txt",
        extracted_text=material_text
    )
    db.add(content)
    db.commit()
    db.refresh(content)

    print(f"Created test content: {content.id}")

    # Extract knowledge graph
    service = KnowledgeGraphService(db)

    print("\nExtracting knowledge graph...")
    result = await service.extract_knowledge_graph(content.id)

    print(f"\nExtraction complete!")
    print(f"Concepts found: {result['stats']['concept_count']}")
    print(f"Dependencies found: {result['stats']['dependency_count']}")

    print("\nConcepts:")
    for concept in result['concepts'][:5]:  # First 5
        print(f"  - {concept['name']} ({concept['difficulty']})")
        print(f"    {concept['description'][:100]}...")

    print("\nDependencies:")
    for dep in result['dependencies'][:5]:  # First 5
        print(f"  - {dep['prerequisite']} → {dep['concept']} ({dep['strength']})")

    db.close()


if __name__ == "__main__":
    asyncio.run(test_extraction())
```

### Task 4.3: Run and Validate

```bash
cd backend
python tests/scripts/test_knowledge_graph_extraction.py
```

**Expected output:**
```
Created test content: 123e4567-e89b-12d3-a456-426614174000

Extracting knowledge graph...

Extraction complete!
Concepts found: 12
Dependencies found: 18

Concepts:
  - Variables (beginner)
    Understanding how to declare and use variables to store data...
  - Data Types (beginner)
    Different types of data in C: int, float, char, string...
  - Operators (beginner)
    Arithmetic and logical operators for manipulating data...
  - Conditionals (intermediate)
    Making decisions with if/else statements...
  - Loops (intermediate)
    Repeating actions with for and while loops...

Dependencies:
  - Variables → Data Types (required)
  - Variables → Operators (required)
  - Operators → Conditionals (required)
  - Conditionals → Loops (recommended)
  - Data Types → Arrays (required)
```

**Deliverable**: Proven extraction from real CS50 materials

---

## Success Criteria for Week 1

### Must Have ✅
- [ ] Database tables created and migrated
- [ ] SQLAlchemy models working with CRUD operations
- [ ] Knowledge Graph Service extracts concepts from text
- [ ] Knowledge Graph Service identifies dependencies
- [ ] API endpoints accessible and documented
- [ ] Tested with real CS50 Week 1 materials
- [ ] Extract at least 10 concepts with 80%+ accuracy
- [ ] Identify at least 15 dependencies with 70%+ correctness

### Nice to Have 🎯
- [ ] Graph visualization in frontend (simple D3.js or cytoscape)
- [ ] Validation UI to correct concept extraction
- [ ] Batch processing for multiple weeks/courses
- [ ] Performance optimization (< 30s extraction time)

### Acceptance Test
Given CS50 Week 1 materials, the system should:
1. Extract atomic concepts (variables, loops, conditionals, etc.)
2. Identify logical prerequisites (variables before arrays)
3. Assign reasonable difficulty levels
4. Store in database with proper relationships
5. Return queryable graph via API

---

## Risk Mitigation

### Risk 1: Claude Extracts Poor Concepts
**Mitigation**:
- Use lower temperature (0.3) for structured output
- Provide clear examples in prompts
- Implement validation logic
- Allow manual correction UI

### Risk 2: Circular Dependencies
**Mitigation**:
- Check for cycles in dependency graph
- Reject circular dependencies
- Prompt Claude to avoid them explicitly

### Risk 3: Too Many Concepts (Overwhelm)
**Mitigation**:
- Aim for 10-20 concepts per week of content
- Merge overly granular concepts
- Focus on "atomic but teachable" units

### Risk 4: Extraction Takes Too Long
**Mitigation**:
- Process in background task
- Show progress indicator
- Cache results
- Consider batch processing

---

## Next Steps (Week 2)

After completing Week 1, move to practice problem generation:
- Generate coding exercises for each concept
- Create test cases for auto-grading
- Implement code execution sandbox
- Build practice problem UI

---

**Questions? Issues? Document them and adapt the plan as needed.**

This is an iterative process - Week 1 sets the foundation, but expect to refine based on what you learn from real CS50 materials.
