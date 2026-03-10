# Study Architect Consolidation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate ai-study-architect from its nested location inside cs50/, reorganize 33+ docs into a clean structure, integrate Stitch design assets, and rewrite README/CLAUDE.md to reflect the mastery-based MVP — all without losing any valuable content.

**Architecture:** The repo `belumume/ai-study-architect` is currently cloned at `C:/Users/elzai/DEV/cs50/project/`. It gets moved to `C:/Users/elzai/DEV/ai-study-architect/`. Documentation is reorganized into `technical/`, `vision/`, `direction/`, `planning/`, `archive/` subdirectories. Stitch export is extracted into a new `design/` folder. README and CLAUDE.md are rewritten to reflect honest current state (~25% built, mastery-based pivot).

**Tech Stack:** Git, bash (MSYS2/Git Bash on Windows 11), Python for zip extraction

**Design doc:** `docs/plans/2026-03-10-consolidation-design.md`

**Important:** The repo is currently on branch `claude/clarify-dev-pickup-011CUMHBGkDmsT5SQgh5DjPu` and is 5 commits behind `origin/main`. All work happens on a fresh branch from main.

---

### Task 1: Sync local repo and create consolidation branch

**Files:**
- None modified yet — git operations only

**Step 1: Switch to main and pull latest**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
git stash  # Save any uncommitted work
git checkout main
git pull origin main
```

Expected: Branch switches to main, pulls 5 new commits.

**Step 2: Create consolidation branch**

```bash
git checkout -b consolidation/docs-reorg-and-cleanup
```

Expected: New branch created from latest main.

**Step 3: Commit the design docs (already created)**

```bash
git add docs/plans/
git commit -m "$(cat <<'EOF'
docs: add consolidation design doc and implementation plan

Design doc covers full repo reorganization strategy:
- Doc categorization (33 files analyzed)
- Archive vs keep decisions
- Stitch design pipeline
- README/CLAUDE.md rewrite specs

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: Clean commit with both plan files.

---

### Task 2: Create target directory structure

**Files:**
- Create: `docs/technical/` (directory)
- Create: `docs/vision/` (directory)
- Create: `docs/direction/` (directory)
- Create: `docs/planning/` (directory)
- Create: `design/stitch/v1-analytics-pro/` (directory)

**Step 1: Create all target directories**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
mkdir -p docs/technical docs/vision docs/direction docs/planning design/stitch/v1-analytics-pro
```

Expected: Directories created. `docs/archive/` already exists.

**Step 2: Add .gitkeep files so git tracks empty dirs**

```bash
touch docs/technical/.gitkeep docs/vision/.gitkeep docs/direction/.gitkeep docs/planning/.gitkeep design/.gitkeep design/stitch/.gitkeep design/stitch/v1-analytics-pro/.gitkeep
```

**Step 3: Commit directory structure**

```bash
git add docs/technical/ docs/vision/ docs/direction/ docs/planning/ design/
git commit -m "$(cat <<'EOF'
chore: create target directory structure for doc reorganization

New subdirectories:
- docs/technical/ — active technical docs
- docs/vision/ — product DNA (Karpathy, PG, genesis)
- docs/direction/ — current strategic direction
- docs/planning/ — active sprint planning
- design/stitch/ — Stitch design assets pipeline

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Move docs into technical/

**Files:**
- Move: `docs/API_REFERENCE.md` → `docs/technical/API_REFERENCE.md`
- Move: `docs/ARCHITECTURE.md` → `docs/technical/ARCHITECTURE.md`
- Move: `docs/IMPLEMENTATION_STATUS.md` → `docs/technical/IMPLEMENTATION_STATUS.md`
- Move: `docs/GLOSSARY.md` → `docs/technical/GLOSSARY.md`

**Step 1: Move technical docs**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
git mv docs/API_REFERENCE.md docs/technical/
git mv docs/ARCHITECTURE.md docs/technical/
git mv docs/IMPLEMENTATION_STATUS.md docs/technical/
git mv docs/GLOSSARY.md docs/technical/
```

**Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs: move technical docs to docs/technical/

Moved: API_REFERENCE, ARCHITECTURE, IMPLEMENTATION_STATUS, GLOSSARY
These are active technical docs describing what IS built.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Move docs into vision/

**Files:**
- Move: `docs/COLLECTIVE_INTELLIGENCE_VISION.md` → `docs/vision/`
- Move: `docs/GREAT_WORK_ALIGNMENT.md` → `docs/vision/`
- Move: `docs/GREAT_WORK_VISION.md` → `docs/vision/`
- Move: `docs/PROBLEM_STATEMENT.md` → `docs/vision/`
- Move: `docs/PROJECT_GENESIS.md` → `docs/vision/`
- Move: `docs/archive/PHILOSOPHY.md` → `docs/vision/` (rescued)

**Step 1: Move vision docs**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
git mv docs/COLLECTIVE_INTELLIGENCE_VISION.md docs/vision/
git mv docs/GREAT_WORK_ALIGNMENT.md docs/vision/
git mv docs/GREAT_WORK_VISION.md docs/vision/
git mv docs/PROBLEM_STATEMENT.md docs/vision/
git mv docs/PROJECT_GENESIS.md docs/vision/
git mv docs/archive/PHILOSOPHY.md docs/vision/
```

**Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs: move vision/aspirational docs to docs/vision/

Product DNA — WHY this exists:
- Karpathy "uplift team human" (COLLECTIVE_INTELLIGENCE_VISION)
- Paul Graham "Great Work" framework (GREAT_WORK_ALIGNMENT, GREAT_WORK_VISION)
- AI Learning Paradox (PROBLEM_STATEMENT)
- Origin story (PROJECT_GENESIS)
- Core philosophy (PHILOSOPHY — rescued from archive)

These aren't actionable for the MVP but represent the product's purpose.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Move docs into direction/ and planning/

**Files:**
- Move: `docs/NEW_DIRECTION_2025.md` → `docs/direction/`
- Move: `docs/IMPLEMENTATION_PLAN_WEEK1.md` → `docs/planning/`
- Move: `DAILY_DEV_PLAN.md` (root) → `docs/planning/`

**Step 1: Move direction and planning docs**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
git mv docs/NEW_DIRECTION_2025.md docs/direction/
git mv docs/IMPLEMENTATION_PLAN_WEEK1.md docs/planning/
git mv DAILY_DEV_PLAN.md docs/planning/
```

**Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs: move strategic direction and planning docs

- docs/direction/NEW_DIRECTION_2025.md — CANONICAL strategic document
- docs/planning/IMPLEMENTATION_PLAN_WEEK1.md — active sprint
- docs/planning/DAILY_DEV_PLAN.md — moved from root

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Move superseded docs into archive/

**Files:**
- Move: `STRATEGIC_PIVOT_SUMMARY.md` (root) → `docs/archive/`
- Move: `DOCUMENTATION_AUDIT.md` (root) → `docs/archive/`
- Move: `CRITICAL_NOTES.md` (root) → `docs/archive/`
- Move: `CRITICAL_SESSION_SUMMARY_AUG_2025.md` (root) → `docs/archive/`
- Move: `docs/PRAGMATIC_EXECUTION.md` → `docs/archive/`
- Move: `docs/DOCUMENTATION_SYNCHRONIZATION_PLAN.md` → `docs/archive/`
- Move: `docs/DOCUMENTATION_HIERARCHY.md` → `docs/archive/`
- Move: `docs/AGENT_EVOLUTION.md` → `docs/archive/`
- Move: `docs/UNIQUE_VALUE_PROPOSITION.md` → `docs/archive/`
- Move: `docs/GREAT_WORK_QUICK_REFERENCE.md` → `docs/archive/`
- Move: `docs/guides/ai-study-architect-implementation-guide.md` → `docs/archive/implementation-guide.md`
- Move: `docs/planning/perfect-cs50-ai-project-2025.md` → `docs/archive/`
- Move: `docs/requirements/cs50-final-project-requirements.md` → `docs/archive/`

**Step 1: Move root-level superseded docs**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
git mv STRATEGIC_PIVOT_SUMMARY.md docs/archive/
git mv DOCUMENTATION_AUDIT.md docs/archive/
git mv CRITICAL_NOTES.md docs/archive/
git mv CRITICAL_SESSION_SUMMARY_AUG_2025.md docs/archive/
```

**Step 2: Move docs/ level superseded docs**

```bash
git mv docs/PRAGMATIC_EXECUTION.md docs/archive/
git mv docs/DOCUMENTATION_SYNCHRONIZATION_PLAN.md docs/archive/
git mv docs/DOCUMENTATION_HIERARCHY.md docs/archive/
git mv docs/AGENT_EVOLUTION.md docs/archive/
git mv docs/UNIQUE_VALUE_PROPOSITION.md docs/archive/
git mv docs/GREAT_WORK_QUICK_REFERENCE.md docs/archive/
git mv docs/guides/ai-study-architect-implementation-guide.md docs/archive/implementation-guide.md
git mv docs/planning/perfect-cs50-ai-project-2025.md docs/archive/
git mv docs/requirements/cs50-final-project-requirements.md docs/archive/
```

**Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs: archive superseded docs (nothing deleted)

Moved to docs/archive/:
- STRATEGIC_PIVOT_SUMMARY (superseded by NEW_DIRECTION_2025)
- PRAGMATIC_EXECUTION (superseded by NEW_DIRECTION_2025)
- DOCUMENTATION_AUDIT, DOCUMENTATION_SYNCHRONIZATION_PLAN, DOCUMENTATION_HIERARCHY (meta-docs)
- AGENT_EVOLUTION (7-agent history, superseded by mastery pivot)
- UNIQUE_VALUE_PROPOSITION (pre-pivot framing)
- GREAT_WORK_QUICK_REFERENCE (derivative)
- implementation-guide (outdated timeline)
- perfect-cs50-ai-project-2025, cs50-final-project-requirements
- CRITICAL_NOTES, CRITICAL_SESSION_SUMMARY_AUG_2025

All preserved. See docs/direction/NEW_DIRECTION_2025.md for current strategy.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Delete the 7 truly disposable files

**Files:**
- Delete: `docs/archive/BALANCE.md`
- Delete: `docs/archive/CLAUDE_SESSION_24.md`
- Delete: `docs/archive/CLAUDE_SESSIONS.md`
- Delete: `docs/archive/FINAL_BROWSER_FIX_INSTRUCTIONS.md`
- Delete: `docs/archive/FORCE_BROWSER_REFRESH.md`
- Delete: `docs/archive/PROBLEM_STATEMENT.md` (duplicate of root version, now in vision/)
- Delete: `docs/archive/PROMPT_VERIFICATION_CHECKLIST.md`

**Step 1: Verify each file exists and is truly disposable**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
wc -l docs/archive/BALANCE.md docs/archive/CLAUDE_SESSION_24.md docs/archive/CLAUDE_SESSIONS.md docs/archive/FINAL_BROWSER_FIX_INSTRUCTIONS.md docs/archive/FORCE_BROWSER_REFRESH.md docs/archive/PROBLEM_STATEMENT.md docs/archive/PROMPT_VERIFICATION_CHECKLIST.md 2>/dev/null
```

Expected: File sizes confirm these are session logs, one-off fixes, duplicates.

**Step 2: Delete files**

```bash
git rm docs/archive/BALANCE.md docs/archive/CLAUDE_SESSION_24.md docs/archive/CLAUDE_SESSIONS.md docs/archive/FINAL_BROWSER_FIX_INSTRUCTIONS.md docs/archive/FORCE_BROWSER_REFRESH.md docs/archive/PROBLEM_STATEMENT.md docs/archive/PROMPT_VERIFICATION_CHECKLIST.md
```

**Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs: remove 7 truly disposable files from archive

Deleted (zero lasting value):
- BALANCE.md — empty fragment
- CLAUDE_SESSION_24.md, CLAUDE_SESSIONS.md — session transcripts
- FINAL_BROWSER_FIX_INSTRUCTIONS.md, FORCE_BROWSER_REFRESH.md — one-off debugging
- PROBLEM_STATEMENT.md — duplicate (canonical version in docs/vision/)
- PROMPT_VERIFICATION_CHECKLIST.md — obsolete QA process

All other docs preserved. Git history retains full content.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Write archive/README.md

**Files:**
- Create: `docs/archive/README.md`

**Step 1: Write the archive README**

Create `docs/archive/README.md` with this content:

```markdown
# Archived Documentation

These documents are **superseded** by current strategy but preserved for historical context and valuable ideas.

**Current strategic direction:** See [`docs/direction/NEW_DIRECTION_2025.md`](../direction/NEW_DIRECTION_2025.md)

## Why these are archived

The project went through several pivots:
1. Original 7-agent Socratic chatbot vision (July 2025)
2. Collective Intelligence expansion (August 2025, Karpathy challenge)
3. Mastery-based learning pivot (October 2025) — **current direction**

Documents from phases 1-2 that don't align with the mastery-based MVP are archived here. Valuable ideas (collective intelligence, spaced repetition scheduling, knowledge graphs) are preserved in `docs/vision/` for future phases.

## Contents

| File | Original Purpose | Why Archived |
|------|-----------------|--------------|
| STRATEGIC_PIVOT_SUMMARY.md | Early pivot summary | Superseded by NEW_DIRECTION_2025.md |
| PRAGMATIC_EXECUTION.md | Minimal execution path | Absorbed into NEW_DIRECTION_2025.md |
| AGENT_EVOLUTION.md | 7-agent architecture history | Pivot away from agent-count focus |
| UNIQUE_VALUE_PROPOSITION.md | Pre-pivot UVP | Socratic agent framing outdated |
| DOCUMENTATION_AUDIT.md | Doc quality audit | Findings addressed by this reorganization |
| DOCUMENTATION_SYNCHRONIZATION_PLAN.md | Doc sync process | Superseded by this reorganization |
| DOCUMENTATION_HIERARCHY.md | Doc authority levels | No longer needed with clean structure |
| GREAT_WORK_QUICK_REFERENCE.md | PG quick reference | Derivative of GREAT_WORK_ALIGNMENT (in vision/) |
| implementation-guide.md | 10-week roadmap | Timeline outdated, patterns useful |
| perfect-cs50-ai-project-2025.md | CS50 planning | Pre-pivot planning doc |
| cs50-final-project-requirements.md | CS50 requirements | Kept for eventual submission reference |
| CRITICAL_NOTES.md | Session notes | Historical context |
| CRITICAL_SESSION_SUMMARY_AUG_2025.md | Session summary | Historical context |
| DISCOVERIES.md | Lessons learned | Historical reference |
| EXPERIMENTS.md | Experimental approaches | Historical reference |
| COMPLETE_FIX_SUMMARY.md | Major fix cycle | Debugging reference |
| AUDIT_VERIFICATION_PROTOCOL.md | QA process | Template for future audits |
```

**Step 2: Commit**

```bash
git add docs/archive/README.md
git commit -m "$(cat <<'EOF'
docs: add archive README explaining why docs are preserved

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Weed ARCHITECTURE.md (remove 7-agent claims)

**Files:**
- Modify: `docs/technical/ARCHITECTURE.md`

**Step 1: Read current ARCHITECTURE.md fully**

Read `docs/technical/ARCHITECTURE.md` to identify all 7-agent references.

**Step 2: Edit — remove the "Legacy Architecture Note" block and update the "In Active Development" section**

Changes to make:
- Lines referencing "7-agent system" or individual planned agents: remove or replace with mastery-based components
- The "In Active Development" list (knowledge graph, practice generator, mastery tracker, etc.): update to reflect these are Phase 2, not current sprint
- The "Legacy Architecture Note" (line 32-34): remove — the archive README now covers this context
- Keep: Security architecture, backend/frontend file trees, database schema, service-oriented principles, development workflow

**Step 3: Commit**

```bash
git add docs/technical/ARCHITECTURE.md
git commit -m "$(cat <<'EOF'
docs: weed ARCHITECTURE.md — remove 7-agent claims, clarify MVP scope

- Removed legacy architecture note (context now in archive/README)
- Clarified "In Active Development" items as Phase 2
- Kept: security, backend/frontend structure, DB schema, principles

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Add vision header to GREAT_WORK_VISION.md

**Files:**
- Modify: `docs/vision/GREAT_WORK_VISION.md`

**Step 1: Add status header after the frontmatter**

Insert after line 9 (after `Status: Active`):

```markdown
> **Scope Note**: This document captures long-term aspirational vision. Items like "adversarial agents" and "emotion-aware tutoring" are future explorations, not part of the current MVP. See [`docs/direction/NEW_DIRECTION_2025.md`](../direction/NEW_DIRECTION_2025.md) for current scope.
```

**Step 2: Commit**

```bash
git add docs/vision/GREAT_WORK_VISION.md
git commit -m "$(cat <<'EOF'
docs: add scope note to GREAT_WORK_VISION.md

Clarifies aspirational items are long-term vision, not current MVP.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: Extract Stitch export and PRD into design/

**Files:**
- Extract: `C:\Users\elzai\PC\Downloads\stitch (1).zip` → `design/stitch/v1-analytics-pro/`
- Copy: `C:\Users\elzai\DEV\Analytics Pro Study Companion PRD.txt` → `design/PRD.md`
- Create: `design/README.md`

**Step 1: Extract the Stitch zip**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
python -c "
import zipfile, shutil, os
z = zipfile.ZipFile('C:/Users/elzai/PC/Downloads/stitch (1).zip')
z.extractall('design/stitch/v1-analytics-pro/')
z.close()
# The zip contains analytics_pro_study_companion_prd.html and stitch/ subfolder
# Move contents from stitch/ subfolder up if nested
nested = 'design/stitch/v1-analytics-pro/stitch'
if os.path.isdir(nested):
    for item in os.listdir(nested):
        shutil.move(os.path.join(nested, item), 'design/stitch/v1-analytics-pro/')
    os.rmdir(nested)
print('Extracted successfully')
"
```

Expected: `design/stitch/v1-analytics-pro/` contains `dashboard/`, `active_focus_session/`, `subject_detail/`, `weekly_analytics/`, and the PRD HTML.

**Step 2: Copy PRD text as markdown**

```bash
cp "C:/Users/elzai/DEV/Analytics Pro Study Companion PRD.txt" "C:/Users/elzai/DEV/cs50/project/design/PRD.md"
```

**Step 3: Write design/README.md**

Create `design/README.md` with this content:

```markdown
# Design Assets — Study Architect

## Stitch Design Pipeline

Study Architect's frontend design is generated and iterated using [Google Stitch](https://stitch.withgoogle.com/) (AI UI design tool).

### Workflow

```
Stitch (cloud) ──export──→ design/stitch/ ──react-components skill──→ frontend/src/
       ↑                                                                    │
       └──── iterate via stitch-loop skill / edit_screens MCP ←────────────┘
```

### Current Assets

**v1-analytics-pro/** — Initial Ideate mode output (Analytics Pro direction only)
- `dashboard/` — Main dashboard with activity heatmap, subject progress, daily timer
- `active_focus_session/` — Focus timer with telemetry indicators
- `subject_detail/` — Per-subject analytics with velocity chart and efficiency scores
- `weekly_analytics/` — Weekly review with peak performance, focus degradation, allocation
- `analytics_pro_study_companion_prd.html` — Generated PRD document (rendered)

**v2-mixed/** — TO BE GENERATED: Mixed directions (Analytics Pro + Zen Study + Gamification)

### Design System

- **Theme**: Dark mode, "tactical cyberpunk telemetry"
- **Colors**: Deep black surfaces, neon cyan/chartreuse (#ccf20d) accents
- **Typography**: Space Grotesk (headings), monospace (data)
- **See**: `PRD.md` for full design system with CSS tokens

### Stitch Project

- **ID**: `10211254190976208744`
- **MCP**: `mcp__stitch__*` tools for programmatic access
- **Skills**: react-components, design-md, enhance-prompt, stitch-loop, remotion, shadcn-ui
```

**Step 4: Remove .gitkeep files (real content exists now)**

```bash
rm -f design/.gitkeep design/stitch/.gitkeep design/stitch/v1-analytics-pro/.gitkeep
```

**Step 5: Commit**

```bash
git add design/
git commit -m "$(cat <<'EOF'
feat: add Stitch design assets and pipeline documentation

- Extracted Analytics Pro Stitch export (4 screens + PRD HTML)
- Added PRD.md (full design system with CSS tokens)
- Added design/README.md documenting Stitch workflow
- v2-mixed/ placeholder for upcoming mixed-directions iteration

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 12: Write new docs/README.md (navigation index)

**Files:**
- Create (or overwrite): `docs/README.md`

**Step 1: Write the docs index**

Create `docs/README.md`:

```markdown
# Documentation — Study Architect

## Quick Navigation

### Current Direction
- [`direction/NEW_DIRECTION_2025.md`](direction/NEW_DIRECTION_2025.md) — **Start here.** Canonical strategic document (Oct 2025 mastery-based pivot)

### Technical Reference
- [`technical/ARCHITECTURE.md`](technical/ARCHITECTURE.md) — System architecture and components
- [`technical/API_REFERENCE.md`](technical/API_REFERENCE.md) — API endpoint documentation
- [`technical/IMPLEMENTATION_STATUS.md`](technical/IMPLEMENTATION_STATUS.md) — What's built vs planned
- [`technical/GLOSSARY.md`](technical/GLOSSARY.md) — Standardized terminology

### Active Planning
- [`planning/DAILY_DEV_PLAN.md`](planning/DAILY_DEV_PLAN.md) — Current sprint breakdown
- [`planning/IMPLEMENTATION_PLAN_WEEK1.md`](planning/IMPLEMENTATION_PLAN_WEEK1.md) — Week 1 detailed plan
- [`plans/`](plans/) — Design documents and implementation plans

### Vision & Product DNA
- [`vision/PROBLEM_STATEMENT.md`](vision/PROBLEM_STATEMENT.md) — The AI Learning Paradox
- [`vision/PROJECT_GENESIS.md`](vision/PROJECT_GENESIS.md) — How this project was born
- [`vision/PHILOSOPHY.md`](vision/PHILOSOPHY.md) — Core building principles
- [`vision/COLLECTIVE_INTELLIGENCE_VISION.md`](vision/COLLECTIVE_INTELLIGENCE_VISION.md) — Karpathy "uplift team human"
- [`vision/GREAT_WORK_ALIGNMENT.md`](vision/GREAT_WORK_ALIGNMENT.md) — Paul Graham framework
- [`vision/GREAT_WORK_VISION.md`](vision/GREAT_WORK_VISION.md) — Long-term aspirational vision

### Design
- [`../design/README.md`](../design/README.md) — Stitch design pipeline and assets
- [`../design/PRD.md`](../design/PRD.md) — Analytics Pro product requirements

### Archive
- [`archive/`](archive/) — Superseded docs, preserved for historical context
```

**Step 2: Delete old DOCUMENTATION_INDEX.md if it exists at root**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
git rm DOCUMENTATION_INDEX.md 2>/dev/null || true
```

**Step 3: Commit**

```bash
git add docs/README.md
git commit -m "$(cat <<'EOF'
docs: add navigation index for reorganized documentation

Replaces DOCUMENTATION_INDEX.md with structured docs/README.md.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 13: Rewrite README.md

**Files:**
- Overwrite: `README.md` (root)

**Step 1: Read the current README.md one more time to preserve any content worth keeping**

Read `README.md` fully. Preserve: setup instructions, tech stack details, challenges section. Remove: 7-agent claims, collective intelligence as current feature, "7 specialized agents orchestrating together".

**Step 2: Write new README.md**

```markdown
# Study Architect

**Mastery-based AI study companion that proves you learned it.**

*By [Quantelect](https://quantelect.com)*

---

## Status

MVP in progress (~25% of full vision built):

| Component | Status |
|-----------|--------|
| User authentication (JWT/RS256) | Live |
| File upload & content extraction | Live |
| Lead Tutor Agent (Socratic chat) | Live |
| Streaming AI responses (SSE) | Live |
| Analytics dashboard | Designed ([see mockups](design/)) |
| Subject time tracking | Planned |
| Knowledge graphs | Phase 2 |
| Spaced repetition (SM-2) | Phase 2 |
| Mastery gates (90%+) | Phase 2 |

**Live**: [ai-study-architect.onrender.com](https://ai-study-architect.onrender.com) | [aistudyarchitect.com](https://aistudyarchitect.com)

## The Problem

**86% of students use AI in their studies, yet research shows they perform worse when AI support is removed.**

Students are creating cognitive debt instead of building cognitive strength. MIT research reveals AI tools reduce cognitive engagement. Swiss studies find AI usage correlates with reduced critical thinking. UPenn found students performed worse after their AI tutor was removed.

Current AI tools optimize for quick answers, not capability. Study Architect takes the opposite approach.

## The Solution

Study Architect builds cognitive strength through mastery-based learning:

- **Guided discovery** — Socratic questioning that leads to insight, not answers
- **Personalized to YOUR materials** — Upload lectures, PDFs, notes; the AI understands your specific content
- **Measurable retention** — Prove you learned it before moving on (planned: 90%+ mastery gates)
- **Analytics dashboard** — Track study time, subject progress, and learning velocity

The design follows a "tactical cyberpunk telemetry" aesthetic — see [`design/PRD.md`](design/PRD.md) for the full design system.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python), SQLAlchemy, Alembic |
| Frontend | React 18, TypeScript, Material-UI |
| Database | PostgreSQL 17 |
| AI | Claude API (primary), OpenAI (fallback), LangChain |
| Auth | JWT (RS256) with CSRF protection |
| Hosting | Render (backend), Vercel (frontend), Cloudflare (routing) |

## Running Locally

### Prerequisites
- Python 3.11+, Node.js 18+, PostgreSQL 14+
- API keys: Claude (primary) or OpenAI (fallback)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

Environment variables: see `.env.example` in both directories.

## Documentation

- **[Current direction](docs/direction/NEW_DIRECTION_2025.md)** — Mastery-based pivot rationale
- **[Architecture](docs/technical/ARCHITECTURE.md)** — System design and components
- **[Design assets](design/)** — Stitch mockups and design system
- **[Full docs index](docs/README.md)** — All documentation organized by category

## Vision

This project was born from a CS50 final project brainstorming session and grew into something larger. The long-term vision includes collective intelligence, spaced repetition scheduling, and knowledge graphs — see [`docs/vision/`](docs/vision/) for the aspirational roadmap including insights from Andrej Karpathy's "uplift team human" challenge and Paul Graham's "How to Do Great Work" framework.

## License

All rights reserved. Copyright Quantelect.
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: rewrite README to reflect honest current state

- Removed 7-agent claims and collective intelligence as current feature
- Added status table showing what's built vs planned vs Phase 2
- Honest ~25% complete assessment
- Links to design assets, docs index, vision folder
- Branded as Study Architect by Quantelect

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 14: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (root)

**Step 1: Read current CLAUDE.md fully**

Read to identify all sections. Preserve: development commands, platform-specific considerations, troubleshooting table, critical reminders that are still valid.

**Step 2: Update these sections**

Changes:
- **Project Overview**: Replace "7-agent Socratic chatbot" framing with mastery-based MVP. Remove "Current Phase: Strategic pivot" — the pivot is done, this IS the direction now.
- **High-Level Architecture > Planned Components**: Mark knowledge graph, practice generator, mastery tracker, spaced repetition, retention analyzer as "Phase 2 — not in MVP scope"
- **High-Level Architecture > Legacy Reference**: Remove this section (context now in `docs/archive/README.md`)
- **Database > Planned tables**: Mark as Phase 2
- **Quick doc references**: Update paths to new locations (`docs/direction/NEW_DIRECTION_2025.md`, `docs/planning/DAILY_DEV_PLAN.md`)
- **Add**: `## Design Direction` section pointing to `design/PRD.md` and Stitch project
- **Add**: `## Related Repos` section — `quantelect/` (company), `cs50/` (course history)

Keep everything else as-is (commands, security notes, platform notes, troubleshooting).

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs: update CLAUDE.md — MVP scope, design direction, updated paths

- Pivot framing replaced with settled mastery-based direction
- Phase 2 items clearly marked
- Added design direction section (Stitch assets)
- Updated doc paths after reorganization
- Removed legacy architecture reference (now in archive/)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 15: Clean up empty directories and old docs/README.md

**Files:**
- Delete: `docs/guides/` (empty after moving implementation-guide.md)
- Delete: `docs/requirements/` (empty after moving cs50-final-project-requirements.md)
- Modify: Remove `.gitkeep` files from dirs that now have real content

**Step 1: Remove empty directories**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
rmdir docs/guides 2>/dev/null || true
rmdir docs/requirements 2>/dev/null || true
rm -f docs/technical/.gitkeep docs/vision/.gitkeep docs/direction/.gitkeep docs/planning/.gitkeep
```

**Step 2: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
chore: clean up empty directories and gitkeep files

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 16: Verify final state and push

**Step 1: Verify doc structure matches design**

```bash
cd "C:/Users/elzai/DEV/cs50/project"
echo "=== docs/technical ===" && ls docs/technical/
echo "=== docs/vision ===" && ls docs/vision/
echo "=== docs/direction ===" && ls docs/direction/
echo "=== docs/planning ===" && ls docs/planning/
echo "=== docs/archive ===" && ls docs/archive/
echo "=== design ===" && find design/ -type f | sort
```

Expected: All files in their target locations per the design doc.

**Step 2: Verify no docs are orphaned at docs/ root (except README.md and plans/)**

```bash
ls docs/*.md
```

Expected: Only `docs/README.md`.

**Step 3: Verify root-level is clean**

```bash
ls *.md
```

Expected: `README.md`, `CLAUDE.md`, `CLAUDE.local.md`, and operational docs (`BACKUP_SECURITY.md`, `CLOUDFLARE_SETUP.md`, `DEPLOYMENT.md`, `DEVELOPMENT.md`, `SECURITY*.md`, `TROUBLESHOOTING.md`, `VERCEL_ENV_UPDATE.md`, `RENDER_MCP_SECURITY.md`).

**Step 4: Push branch**

```bash
git push -u origin consolidation/docs-reorg-and-cleanup
```

Expected: Branch pushed to GitHub.

**Step 5: Create PR**

```bash
gh pr create --title "docs: consolidate and reorganize project documentation" --body "$(cat <<'EOF'
## Summary

- Reorganized 33+ docs into `technical/`, `vision/`, `direction/`, `planning/`, `archive/` subdirectories
- Deleted 7 truly disposable files (session transcripts, one-off fixes, duplicates)
- Rescued `PHILOSOPHY.md` from archive to `vision/`
- Weeded 7-agent claims from `ARCHITECTURE.md`
- Added scope note to `GREAT_WORK_VISION.md`
- Integrated Stitch design assets into `design/` folder with workflow docs
- Rewrote `README.md` — honest status (~25%), no false claims
- Updated `CLAUDE.md` — MVP scope, design direction, updated doc paths
- Added `docs/README.md` navigation index and `docs/archive/README.md` context

Nothing valuable was deleted. All superseded docs are preserved in `archive/` with clear explanations.

## Test plan

- [ ] Verify all internal doc links resolve correctly
- [ ] Verify `design/stitch/v1-analytics-pro/` contains all 4 screen folders + PRD
- [ ] Verify no orphaned .md files at `docs/` root (only README.md)
- [ ] Verify README.md has no 7-agent or collective intelligence claims
- [ ] Verify CLAUDE.md development commands still work

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Task 17: Move local folder from cs50/project/ to DEV/ai-study-architect/

**This happens AFTER the PR is merged**, since we need to push from the current location first.

**Step 1: Move the folder**

```bash
cd "C:/Users/elzai/DEV"
mv cs50/project ai-study-architect
```

Expected: `DEV/ai-study-architect/` exists with full git history. `DEV/cs50/project/` is gone.

**Step 2: Verify git remote still works**

```bash
cd "C:/Users/elzai/DEV/ai-study-architect"
git remote -v
git log --oneline -3
```

Expected: Remote still points to `belumume/ai-study-architect`. All commits intact.

---

### Task 18: Update cs50 repo with pointer

**Files:**
- Modify: `C:/Users/elzai/DEV/cs50/CLAUDE.md` — remove all Study Architect architecture content
- Modify: `C:/Users/elzai/DEV/cs50/README.md` — add final project pointer

**Step 1: Update cs50/CLAUDE.md**

Replace the "Final Project Structure" section (currently references multi-agent architecture) with:

```markdown
### Final Project
The final project (Study Architect) has graduated to its own repository:
- **Local**: `../ai-study-architect/`
- **GitHub**: https://github.com/belumume/ai-study-architect
```

Keep all other cs50 CLAUDE.md content (compile commands, testing tools, pset patterns).

**Step 2: Add final project pointer to cs50/README.md**

Add a section after the pset listing:

```markdown
## Final Project

**Study Architect** — Mastery-based AI study companion

The final project has its own repository: [belumume/ai-study-architect](https://github.com/belumume/ai-study-architect)
```

**Step 3: Clean up stale files**

```bash
cd "C:/Users/elzai/DEV/cs50"
rm -f fix_claude_config.py nul  # Stale files from git status
```

**Step 4: Commit and push**

```bash
cd "C:/Users/elzai/DEV/cs50"
git add CLAUDE.md README.md
git rm fix_claude_config.py nul 2>/dev/null || true
git commit -m "$(cat <<'EOF'
docs: add final project pointer to Study Architect repo

Final project (Study Architect) graduated to its own repository:
https://github.com/belumume/ai-study-architect

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Execution Order Summary

| Task | Description | Depends On |
|------|-------------|-----------|
| 1 | Sync and create branch | — |
| 2 | Create directory structure | 1 |
| 3 | Move → technical/ | 2 |
| 4 | Move → vision/ | 2 |
| 5 | Move → direction/ + planning/ | 2 |
| 6 | Move → archive/ | 2 |
| 7 | Delete 7 disposable files | 6 |
| 8 | Write archive/README.md | 7 |
| 9 | Weed ARCHITECTURE.md | 3 |
| 10 | Add header to GREAT_WORK_VISION.md | 4 |
| 11 | Extract Stitch assets | 2 |
| 12 | Write docs/README.md index | 3-6 |
| 13 | Rewrite README.md | 12 |
| 14 | Update CLAUDE.md | 5, 11 |
| 15 | Clean up empty dirs | 6 |
| 16 | Verify and push | 3-15 |
| 17 | Move local folder | 16 (after PR merge) |
| 18 | Update cs50 repo | 17 |

Tasks 3-6 and 11 can run in parallel. Tasks 9-10 can run in parallel. Everything else is sequential.
