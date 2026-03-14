---
title: "Full Product Build: MUI Prototype → Tailwind v4 Cyberpunk Dashboard"
category: integration-issues
date: 2026-03-14
tags: [tailwind-v4, shadcn-ui, mui-migration, fastapi, stitch-mcp, visx, web-worker, session-state-machine, ci-actions]
module: Frontend + Backend (full stack)
symptom: "MUI light-mode prototype needed complete visual identity transplant + new backend features"
root_cause: "MUI's Material Design DNA fights cyberpunk aesthetic; no subject/session/dashboard APIs existed"
severity: major-feature
resolution_time: "1 session (~6 hours)"
pr: "#25"
---

# Full Product Build: MUI → Tailwind v4 + New Backend APIs

## Problem

Study Architect was a functional MUI prototype (light theme, Roboto, `#f5f5f5`) with only chat + content upload. Needed: cyberpunk telemetry dashboard (void black, neon chartreuse/cyan), subject management, study session lifecycle, dashboard with real metrics, focus session with timer. The gap between "working prototype" and "shippable product" was the entire visual layer + core tracking features.

## Root Cause

MUI's Material Design opinions (Roboto, elevation shadows, light-mode defaults) are fundamentally incompatible with a cyberpunk telemetry aesthetic. Rethemeing MUI would cost more than replacing it. No backend APIs existed for subjects, sessions, or dashboard aggregation.

## Solution

### Phase -1: Design Iteration
- Used Stitch MCP `edit_screens` to evolve 3 existing mockups (dashboard, subject detail, active focus)
- Removed gamification (XP, levels, badges, ENGAGE buttons)
- Added mastery metrics, recommendations, contribution heatmap
- Downloaded to `design/stitch/v3-evolved/` as implementation reference

### Phase 0: Frontend Foundation
- **Migration ordering** (critical): Install Tailwind + new deps FIRST alongside MUI, rewrite components, THEN remove MUI. Never remove MUI before rewrites — creates uncompilable gap.
- Tailwind v4 CSS-first config with `@theme` block for design tokens
- `@fontsource` imports must be in CSS with `layer(base)` BEFORE `@import "tailwindcss"` — wrong ordering breaks fonts
- shadcn/ui components (button, card, input, dialog, dropdown-menu, tabs, sonner)
- CSP `worker-src: 'self' blob:` — was `'none'` in production, would silently block Web Workers

### Phase 1: Backend + Frontend Features
- **Subject model**: CRUD with unique(user_id, name), auto-assigned colors, max 50, Unicode normalization
- **Session lifecycle**: start/pause/resume/stop with `accumulated_seconds` + `last_resumed_at` for accurate time tracking across pause/resume cycles
- **Partial unique index**: `WHERE status IN ('IN_PROGRESS', 'PAUSED')` prevents concurrent sessions at DB level (uppercase enum values required)
- **Dashboard**: 3 focused queries (NOT single monolithic query) — 28-day aggregation, active session check via partial index, streak via distinct dates
- **Focus page**: Web Worker timer (1000ms setTimeout, NOT 100ms setInterval), Zen aesthetic, keyboard shortcuts (Space/Escape)
- **Dashboard frontend**: HeroMetrics with CSS `@starting-style` staggered reveal, visx ContributionHeatmap with SVG glow filters, TanStack Query with `refetchIntervalInBackground: false`

## Key Bugs Found in Production

1. **`func.timezone()` crash**: SQLAlchemy's `func.timezone()` caused 500 on Neon PostgreSQL. Fixed by removing it — plain `cast(Date)` sufficient for UTC users.
2. **Semgrep `pip install` clobbered deps**: Replaced pydantic, starlette, httpx with incompatible versions. Fixed with `pipx install semgrep`.
3. **Semgrep `p/python-security` 404**: Old config path no longer on registry. Fixed with `--config auto`.
4. **Enum case sensitivity**: PostgreSQL stores SessionStatus as UPPERCASE. Partial index WHERE clause must match.
5. **Rate limiter import**: Module exports `limiter`, not `shared_limiter`.

## Prevention

1. **Always test endpoints on production after deploy** — the dashboard 500 was only caught by post-deploy UI testing via Playwright, not by local tests or CI
2. **Never `pip install` scanning tools into app env** — use `pipx` for isolation
3. **Test SQLAlchemy functions against the actual production DB driver** — func.timezone() worked locally but crashed on Neon
4. **Migration ordering for UI framework swaps**: install new → rewrite → verify build → remove old. Never the reverse.
5. **Verify enum string values against the database** — Python enum `.value` may differ from what PostgreSQL stores

## Compound Engineering Workflow (Full Execution)

This session followed the complete workflow:
```
/brainstorming → /plan → /deepen-plan → /plan_review → /work → /review → /commit-push-pr → UI test → /compound
```

Key learnings about the workflow:
- **Don't skip `/deepen-plan`** — it caught the CSP worker-src showstopper, composite index need, and session state machine design
- **Don't skip code review** — we skipped it initially and pushed, which missed the dashboard 500
- **UI test on DEPLOYED version** — localhost testing is insufficient; production environment differences cause bugs
- **Never cache volatile external data** (model IDs, action versions) — always verify from official docs

## Files Changed

### Backend (new)
- `backend/app/models/subject.py` — Subject model
- `backend/app/schemas/subject.py` — Pydantic schemas with Unicode validation
- `backend/app/api/v1/subjects.py` — CRUD router
- `backend/app/api/v1/study_sessions.py` — Session lifecycle router
- `backend/app/api/v1/dashboard.py` — 3-query dashboard endpoint
- `backend/alembic/versions/942421c3cadb_*.py` — Migration with partial unique index

### Frontend (new)
- `frontend/src/app/layout/` — AppShell, TopNav (replaces MUI AppBar)
- `frontend/src/pages/` — DashboardPage, StudyPage, ContentPage, FocusPage
- `frontend/src/components/dashboard/` — HeroMetrics, SubjectList, ContributionHeatmap, StartFocusCTA
- `frontend/src/hooks/useTimer.ts` — Web Worker timer hook
- `frontend/src/workers/timer.worker.ts` — Accurate background timer
- `frontend/src/index.css` — Tailwind v4 @theme with all design tokens

### Design
- `design/stitch/v3-evolved/` — 4 screens (3 edited, 1 copied)

### CI
- All GitHub Actions updated (checkout@v6, setup-python@v6, setup-node@v6)
- Semgrep migrated from deprecated action to native `pipx install`
- Claude Code Action updated to @v1 with model via `claude_args`
- Node 18 → 20 across all workflows

## Related

- Brainstorm: `docs/brainstorms/2026-03-13-mvp-frontend-brainstorm.md`
- Plan: `docs/plans/2026-03-14-001-feat-full-product-build-phases-neg1-0-1-plan.md`
- SM-2 Research: `~/.claude/projects/.../memory/sm2-fire-mastery-research.md`
- CI Fixes: `~/.claude/projects/.../memory/session8-ci-and-deploy-fixes.md`
