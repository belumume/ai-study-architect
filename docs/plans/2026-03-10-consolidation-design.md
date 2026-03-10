# Study Architect Consolidation Design

**Date**: 2026-03-10
**Status**: Approved
**Scope**: Repo migration, documentation cleanup, Stitch design integration, brand alignment

---

## Context

Study Architect is the first product of Quantelect. Its code lives in `DEV/cs50/project/` (a nested git repo pointing to `belumume/ai-study-architect` on GitHub), while company/pitch materials live in `DEV/quantelect/`. The project has 33 markdown docs in `docs/` plus 6+ root-level markdown files, many contradicting each other due to accumulated pivots (7-agent architecture → unified pipeline → mastery-based MVP). The Oct 2025 mastery-based pivot is the current agreed direction.

### Goals

1. Single source of truth reflecting the mastery-based pivot and scoped MVP
2. Archive outdated docs with clear status markers — nothing valuable deleted
3. Honest README and CLAUDE.md reflecting actual build status (~25%)
4. Stitch design assets integrated as the frontend design direction
5. Clean repo structure suitable for VC/incubator visibility

### Constraints

- Nothing valuable gets deleted, only reorganized
- Karpathy "uplift team human", PG "Great Work", Collective Intelligence Vision preserved as product DNA
- `quantelect/` repo unchanged
- All changes sync to `belumume/ai-study-architect` on GitHub (existing public repo)

---

## 1. Repo Structure

### Current (broken)

```
DEV/
├── cs50/                         ← cs50x-2025-psets-solns repo
│   └── project/                  ← NESTED: ai-study-architect repo (confusing location)
└── quantelect/                   ← quantelect repo (company/pitch)
```

### Target

```
DEV/
├── ai-study-architect/           ← MOVED from cs50/project/ (same git history + remote)
├── cs50/                         ← Course psets only, pointer README for final project
└── quantelect/                   ← Unchanged
```

**Migration method**: `mv cs50/project ai-study-architect` — git doesn't care about folder location. All history, remotes, branches preserved.

---

## 2. Documentation Reorganization

### Target docs/ structure inside ai-study-architect/

```
docs/
├── technical/                    Active technical docs (what IS built)
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md           (weeded: 7-agent refs removed)
│   ├── IMPLEMENTATION_STATUS.md
│   └── GLOSSARY.md
├── vision/                       Product DNA (WHY this exists)
│   ├── COLLECTIVE_INTELLIGENCE_VISION.md   (Karpathy challenge)
│   ├── GREAT_WORK_ALIGNMENT.md             (Paul Graham framework)
│   ├── GREAT_WORK_VISION.md               (header: "long-term, not MVP scope")
│   ├── PROBLEM_STATEMENT.md               (AI Learning Paradox)
│   ├── PROJECT_GENESIS.md                 (origin story)
│   └── PHILOSOPHY.md                      (rescued from archive/)
├── direction/                    Current strategic direction
│   └── NEW_DIRECTION_2025.md              (CANONICAL strategic document)
├── planning/                     Active implementation planning
│   ├── IMPLEMENTATION_PLAN_WEEK1.md
│   └── DAILY_DEV_PLAN.md                  (moved from root)
├── plans/                        Design docs (this file lives here)
│   └── 2026-03-10-consolidation-design.md
├── archive/                      Superseded but preserved
│   ├── README.md                          ("These docs are superseded. See docs/direction/")
│   ├── STRATEGIC_PIVOT_SUMMARY.md         (superseded by NEW_DIRECTION_2025)
│   ├── PRAGMATIC_EXECUTION.md             (superseded by NEW_DIRECTION_2025)
│   ├── DOCUMENTATION_SYNCHRONIZATION_PLAN.md  (superseded by DOCUMENTATION_AUDIT)
│   ├── DOCUMENTATION_HIERARCHY.md
│   ├── DOCUMENTATION_AUDIT.md             (moved from root)
│   ├── AGENT_EVOLUTION.md                 (7-agent history)
│   ├── UNIQUE_VALUE_PROPOSITION.md        (pre-pivot framing)
│   ├── GREAT_WORK_QUICK_REFERENCE.md      (derivative)
│   ├── implementation-guide.md            (outdated timeline)
│   ├── perfect-cs50-ai-project-2025.md
│   ├── cs50-final-project-requirements.md (kept for CS50 submission reference)
│   ├── DISCOVERIES.md
│   ├── EXPERIMENTS.md
│   ├── COMPLETE_FIX_SUMMARY.md
│   └── AUDIT_VERIFICATION_PROTOCOL.md
└── README.md                     Docs index/navigation
```

### Root-level file relocations

| File | Action |
|------|--------|
| `STRATEGIC_PIVOT_SUMMARY.md` | Move to `docs/archive/` |
| `DAILY_DEV_PLAN.md` | Move to `docs/planning/` |
| `DOCUMENTATION_AUDIT.md` | Move to `docs/archive/` |
| `CRITICAL_NOTES.md` | Move to `docs/archive/` |
| `CRITICAL_SESSION_SUMMARY_AUG_2025.md` | Move to `docs/archive/` |
| `DOCUMENTATION_INDEX.md` | Replace with new `docs/README.md` |
| `BACKUP_SECURITY.md` | Keep (operational) |
| `CLOUDFLARE_SETUP.md` | Keep (operational) |
| `DEPLOYMENT.md` | Keep (operational) |
| `DEVELOPMENT.md` | Keep (operational) |
| `SECURITY*.md` (4 files) | Keep (operational) |
| `TROUBLESHOOTING.md` | Keep (operational) |
| `VERCEL_ENV_UPDATE.md` | Keep (operational) |
| `RENDER_MCP_SECURITY.md` | Keep (operational) |

### Files deleted (truly disposable)

Only files with zero lasting value:

| File | Reason |
|------|--------|
| `docs/archive/BALANCE.md` | Empty work-in-progress fragment |
| `docs/archive/CLAUDE_SESSION_24.md` | Session transcript |
| `docs/archive/CLAUDE_SESSIONS.md` | Session transcript index |
| `docs/archive/FINAL_BROWSER_FIX_INSTRUCTIONS.md` | One-off debugging |
| `docs/archive/FORCE_BROWSER_REFRESH.md` | One-off debugging |
| `docs/archive/PROBLEM_STATEMENT.md` | Duplicate of root version |
| `docs/archive/PROMPT_VERIFICATION_CHECKLIST.md` | Obsolete QA process |

**7 files deleted. Everything else preserved.**

### Files needing weeding (mixed current/outdated content)

| File | What's outdated | What stays | Action |
|------|----------------|------------|--------|
| `README.md` (root) | "7 specialized agents", collective intelligence as current feature | Philosophy, problem statement | Full rewrite |
| `ARCHITECTURE.md` | 7-agent architecture sections | Security, mastery flow, DB schema, performance | Remove agent sections, add MVP scope |
| `GREAT_WORK_VISION.md` | "Adversarial agents", "emotion-aware" as near-term | Temporal knowledge graphs, reverse pedagogy | Add header: "Long-term vision — not in MVP scope" |
| `UNIQUE_VALUE_PROPOSITION.md` | Socratic agent framing | Differentiation framework | Archive as-is with status marker |

### File rescued from archive

| File | From | To | Reason |
|------|------|----|--------|
| `PHILOSOPHY.md` | `docs/archive/` | `docs/vision/` | Core product philosophy, still relevant |

---

## 3. Stitch Design Pipeline

### Existing assets

- **Stitch project**: "Analytics Pro Study Companion - PRD" (ID `10211254190976208744`)
  - Dark mode, lime #ccf20d, Space Grotesk, mobile-first
  - 6 screens: 1 PRD document + 4 UI screens + 1 group container
  - "Tactical cyberpunk telemetry" aesthetic
- **Export zip**: `C:\Users\elzai\PC\Downloads\stitch (1).zip`
  - Contains: `prd.html`, `dashboard/`, `active_focus_session/`, `subject_detail/`, `weekly_analytics/`
  - Each screen folder has `code.html` + `screen.png`
- **PRD text**: `C:\Users\elzai\DEV\Analytics Pro Study Companion PRD.txt` (200 lines, full design system)

### Stitch skills installed (all 6)

| Skill | Purpose |
|-------|---------|
| `react-components` | Convert Stitch screens to production React code |
| `design-md` | Generate DESIGN_SYSTEM.md from Stitch project |
| `enhance-prompt` | Improve Stitch generation prompts |
| `stitch-loop` | Multi-page site generation |
| `remotion` | Generate walkthrough videos (CS50 requires video demo) |
| `shadcn-ui` | shadcn/ui component library integration |

### Design iteration plan

```
Phase 1 (consolidation): Extract existing export → design/stitch/v1-analytics-pro/
Phase 2 (mix):           Stitch Ideate mixed directions → design/stitch/v2-mixed/
Phase 3 (build):         react-components skill → frontend/src/
```

**Phase 2 mix prompt** (for Stitch Ideate conversation):
> "Actually, let's mix directions. Use Analytics Pro (dark mode, neon data) for the dashboard and analytics screens. Use Minimalist Zen (calm, minimal) for the active focus session screen. Add subtle gamification elements (streaks, mastery badges, progress visualization) across all screens."

### Target design/ folder

```
design/
├── stitch/
│   ├── v1-analytics-pro/          Existing export
│   │   ├── prd.html
│   │   ├── dashboard/
│   │   ├── active_focus_session/
│   │   ├── subject_detail/
│   │   └── weekly_analytics/
│   └── v2-mixed/                  TO BE GENERATED
├── PRD.md                         Text version of PRD
├── DESIGN_SYSTEM.md               Generated via design-md skill
└── README.md                      Stitch workflow documentation
```

---

## 4. README.md Rewrite

New README reflects honest current state:

- **Title**: Study Architect — by Quantelect
- **One-liner**: Mastery-based AI study companion that proves you learned it
- **Status**: "MVP in progress — auth, file upload, Lead Tutor agent, streaming chat deployed. Analytics dashboard designed (see `design/`). ~25% complete."
- **Problem**: AI Learning Paradox (86% use AI, perform worse without)
- **Solution**: Mastery-based learning with time tracking + analytics
- **Tech stack**: FastAPI, React 18/TypeScript, PostgreSQL, Claude API
- **Design direction**: Link to Stitch project + `design/` folder
- **Vision**: Brief mention of collective intelligence, link to `docs/vision/`
- **Links**: quantelect.com, aistudyarchitect.com (active until July 2027)
- **No claims about**: 7 agents, collective intelligence as current feature, knowledge graphs as built

---

## 5. CLAUDE.md Update

Reflects current reality:

- **Identity**: Study Architect by Quantelect — mastery-based AI learning
- **MVP scope**: FastAPI backend + React frontend + Analytics Pro dashboard (Stitch design), subject time tracking, basic analytics
- **Not in MVP scope**: Knowledge graphs, spaced repetition, mastery gates (Phase 2, see `docs/direction/`)
- **What's built**: Auth, file upload, Lead Tutor Agent, streaming chat, deployment on Render/Vercel
- **Tech**: FastAPI, React 18/TS, PostgreSQL, Claude API
- **Design direction**: Analytics Pro cyberpunk telemetry aesthetic (see `design/PRD.md`)
- **Canonical strategic doc**: `docs/direction/NEW_DIRECTION_2025.md`
- **Related repos**: `quantelect/` (company/pitch), `cs50/` (course history)

---

## 6. cs50/ Repo Changes

One commit to `cs50x-2025-psets-solns`:

- Remove `project/` directory (it's moved to `DEV/ai-study-architect/`)
- Update `README.md` with pointer: "Final project: Study Architect → github.com/belumume/ai-study-architect"
- Keep all pset directories as-is

---

## 7. Domain & Brand

| Domain | Status | Role |
|--------|--------|------|
| `quantelect.com` | 10-year ownership | Company brand, product page |
| `aistudyarchitect.com` | Active until July 2027 (Cloudflare) | Product landing, redirect to quantelect.com/study-architect possible |
| `ubaidullahshuaib.com` | 10-year ownership | Personal site, portfolio links |

Product may get its own unique domain later if there's traction. No action needed now.

---

## 8. GitHub Sync

All changes push to existing remotes:

| Repo | Remote | Action |
|------|--------|--------|
| `ai-study-architect` | `belumume/ai-study-architect` (public) | Doc reorg, README/CLAUDE.md rewrite, design/ folder |
| `cs50x-2025-psets-solns` | `belumume/cs50x-2025-psets-solns` (private) | Remove nested project/, add pointer README |
| `quantelect` | `belumume/quantelect` (private) | No changes |

---

## Summary

| Metric | Count |
|--------|-------|
| Files moved to organized locations | ~30 |
| Files deleted (truly disposable) | 7 |
| Files needing content weeding | 4 |
| Files rescued from archive | 1 |
| New files created | ~5 (design/, docs/README.md, archive/README.md) |
| Repos affected | 2 (ai-study-architect, cs50) |
| Repos unchanged | 1 (quantelect) |
