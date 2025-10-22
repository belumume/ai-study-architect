# Daily Development Plan: 1-2 Hour Sessions

**Philosophy**: Consistency over intensity. Small daily wins compound into major progress.

**Your Schedule**: 1-2 hours per day, working around CS studies

**Approach**: Each session has ONE clear goal. Complete it, commit it, done.

---

## Week 1: Knowledge Graph Foundation (7 days)

### Day 1: Database Schema (1-2 hours)
**Goal**: Create and migrate concept tables

**Tasks**:
- [ ] Create Alembic migration for `concepts` table
- [ ] Create migration for `concept_dependencies` table
- [ ] Run migration locally
- [ ] Test basic CRUD operations

**Win**: Tables exist in database, can insert/query concepts

**Files to create**:
- `backend/alembic/versions/xxx_add_knowledge_graph_tables.py`

**Commit message**: `feat: Add knowledge graph database schema`

---

### Day 2: SQLAlchemy Models (1-2 hours)
**Goal**: Create ORM models for concepts

**Tasks**:
- [ ] Create `backend/app/models/concept.py`
- [ ] Define `Concept` model with all fields
- [ ] Define `ConceptDependency` model
- [ ] Add relationships
- [ ] Test models with simple queries

**Win**: Can create Concept objects and query them

**Commit message**: `feat: Add Concept and ConceptDependency models`

---

### Day 3: Pydantic Schemas (1-2 hours)
**Goal**: Create request/response schemas

**Tasks**:
- [ ] Create `backend/app/schemas/concept.py`
- [ ] Define `ConceptBase`, `ConceptCreate`, `ConceptResponse`
- [ ] Define `ConceptGraph` schema
- [ ] Test schema validation

**Win**: Schemas validate input/output correctly

**Commit message**: `feat: Add concept Pydantic schemas`

---

### Day 4: Extraction Prompts (1-2 hours)
**Goal**: Write Claude prompts for concept extraction

**Tasks**:
- [ ] Create `backend/app/prompts/knowledge_graph_extraction.py`
- [ ] Write `EXTRACT_CONCEPTS_PROMPT`
- [ ] Write `EXTRACT_DEPENDENCIES_PROMPT`
- [ ] Test prompts manually with Claude (copy/paste sample CS50 text)

**Win**: Prompts return reasonable JSON when tested manually

**Commit message**: `feat: Add knowledge graph extraction prompts`

---

### Day 5: Extraction Service Part 1 (1-2 hours)
**Goal**: Build concept extraction logic

**Tasks**:
- [ ] Create `backend/app/services/knowledge_graph_service.py`
- [ ] Implement `__init__` and basic structure
- [ ] Implement `_extract_concepts()` method
- [ ] Test with sample text (even hardcoded)

**Win**: Service can extract concepts from sample CS50 text

**Commit message**: `feat: Add concept extraction service (part 1)`

---

### Day 6: Extraction Service Part 2 (1-2 hours)
**Goal**: Build dependency extraction and saving

**Tasks**:
- [ ] Implement `_extract_dependencies()` method
- [ ] Implement `extract_knowledge_graph()` orchestration
- [ ] Implement `get_knowledge_graph()` retrieval
- [ ] Test full extraction flow

**Win**: Full extraction pipeline works end-to-end

**Commit message**: `feat: Complete knowledge graph extraction service`

---

### Day 7: API Endpoints (1-2 hours)
**Goal**: Expose extraction via REST API

**Tasks**:
- [ ] Create `backend/app/api/v1/knowledge_graph.py`
- [ ] Implement `POST /knowledge-graph/extract/{course_id}`
- [ ] Implement `GET /knowledge-graph/{course_id}`
- [ ] Register routes in `api.py`
- [ ] Test with Postman/curl

**Win**: Can trigger extraction via API and retrieve results

**Commit message**: `feat: Add knowledge graph API endpoints`

---

## Week 2: Testing & Polish (7 days)

### Day 8: Test Fixtures (1 hour)
**Goal**: Get real CS50 materials for testing

**Tasks**:
- [ ] Download CS50 Week 1 lecture notes
- [ ] Save to `backend/tests/fixtures/cs50_week1.txt`
- [ ] Create smaller test samples for unit tests

**Win**: Have real materials ready to test against

**Commit message**: `test: Add CS50 test fixtures`

---

### Day 9: Test Script (1-2 hours)
**Goal**: Create end-to-end test

**Tasks**:
- [ ] Create `backend/tests/scripts/test_knowledge_graph_extraction.py`
- [ ] Test extraction with real CS50 materials
- [ ] Validate concept quality
- [ ] Validate dependency logic

**Win**: Extraction works with real CS50 content

**Commit message**: `test: Add knowledge graph extraction test script`

---

### Day 10: Error Handling (1-2 hours)
**Goal**: Make service robust

**Tasks**:
- [ ] Add try/catch blocks
- [ ] Handle JSON parsing errors gracefully
- [ ] Add logging throughout
- [ ] Test with malformed inputs

**Win**: Service doesn't crash on bad input

**Commit message**: `fix: Add error handling to knowledge graph service`

---

### Day 11: Validation Logic (1-2 hours)
**Goal**: Check extracted concepts for quality

**Tasks**:
- [ ] Detect circular dependencies
- [ ] Validate concept names aren't empty
- [ ] Check difficulty levels are valid
- [ ] Add concept count limits (10-20 per extraction)

**Win**: Only valid concept graphs get saved

**Commit message**: `feat: Add knowledge graph validation`

---

### Day 12: Documentation (1 hour)
**Goal**: Document what we've built

**Tasks**:
- [ ] Add API endpoint docs
- [ ] Document database schema
- [ ] Add usage examples to README
- [ ] Update IMPLEMENTATION_STATUS.md

**Win**: Someone else could understand and use the system

**Commit message**: `docs: Document knowledge graph extraction system`

---

### Day 13: Performance Testing (1-2 hours)
**Goal**: Make extraction fast enough

**Tasks**:
- [ ] Time extraction with different content sizes
- [ ] Add progress indicators
- [ ] Consider caching strategies
- [ ] Test with 5 different CS50 weeks

**Win**: Extraction completes in < 60 seconds

**Commit message**: `perf: Optimize knowledge graph extraction`

---

### Day 14: Week 1-2 Review (1 hour)
**Goal**: Reflect and plan ahead

**Tasks**:
- [ ] Review all commits from 14 days
- [ ] Test full system end-to-end
- [ ] Identify what's working well
- [ ] List what needs improvement
- [ ] Plan Week 3-4 (practice generation)

**Win**: Clear understanding of progress and next steps

**Commit message**: `docs: Add Week 1-2 retrospective`

---

## Session Structure (For Each Day)

### Before coding (5 min)
- [ ] Read today's goal
- [ ] Review task checklist
- [ ] Open relevant files

### During coding (45-90 min)
- [ ] Focus on ONE goal
- [ ] Write code
- [ ] Test as you go
- [ ] Don't gold-plate (good enough > perfect)

### After coding (5-10 min)
- [ ] Run final test
- [ ] Commit with clear message
- [ ] Push to branch
- [ ] Check off tasks in this file
- [ ] Feel the win!

---

## Progress Tracking

Update this daily:

```
Week 1 Progress: [==------] 2/7 days complete
Week 2 Progress: [--------] 0/7 days complete

Total: 2/14 days | 14% complete
```

---

## Flexibility Rules

**If you have less time (30-60 min)**:
- Pick the smallest task from today's goal
- Do just that one thing
- Still counts as a win!

**If you have more time (2-3 hours)**:
- Complete today's goal
- Start tomorrow's goal
- Don't burn out though!

**If you miss a day**:
- No problem! Pick up where you left off
- Consistency matters more than perfection

**If something takes longer than expected**:
- That's normal in development
- Split the goal across 2 days
- Update the plan as you learn

---

## Communication with Claude

**Start each session**:
```
"Starting Day X: [Goal]"
```

**I'll help you**:
- Write the code for that day's task
- Debug issues
- Explain concepts
- Keep you on track
- Celebrate the win

**End each session**:
```
"Completed Day X: [what you built]"
```

---

## Why This Works

**Small daily wins**:
- Visible progress every session
- No overwhelming tasks
- Easy to maintain motivation

**Clear goals**:
- Know exactly what you're building
- No decision fatigue
- Can start coding immediately

**Compounding**:
- Day 1: Database tables
- Day 7: Working API
- Day 14: Full extraction system
- Day 30: Practice generation
- Day 60: Mastery gates + spaced repetition
- Day 90: Complete system!

**Consistency > Intensity**:
- 1 hour/day × 90 days = 90 hours
- That's 2 weeks of full-time work
- But sustainable around school

---

## Milestones

- **Day 7**: Knowledge graph extraction working
- **Day 14**: Tested with real CS50 materials
- **Day 30**: Practice problem generation
- **Day 45**: Auto-grading system
- **Day 60**: Mastery gates implemented
- **Day 75**: Spaced repetition working
- **Day 90**: First real user test!

---

## The Meta-Irony

You're building a mastery-based learning system...
...by using mastery-based learning yourself!

Each day = one atomic concept
Each week = one major skill
Spaced repetition = reviewing old code
Mastery gates = tests passing before moving on

**You're dogfooding the philosophy.** That's beautiful.

---

**Ready for Day 1?** Just say "Start Day 1" when you have your next 1-2 hour session!
