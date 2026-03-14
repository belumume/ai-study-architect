---
title: "Full Product Build: MUI Prototype to Tailwind v4 Cyberpunk Dashboard"
category: integration-issues
date: 2026-03-14
tags: [tailwind-v4, shadcn-ui, mui-migration, fastapi, stitch-mcp, visx, web-worker, session-state-machine, ci-actions, compound-engineering]
module: Frontend + Backend (full stack)
symptoms:
  - "MUI light-mode prototype needed complete visual identity transplant"
  - "No subject/session/dashboard APIs existed"
  - "shadcn batch install silently created no files"
  - "husky init failed: .git can't be found from frontend/"
  - "CSP worker-src: 'none' would silently block Web Worker in production"
  - "StudySession schema had id: int but model uses UUID"
  - "Alembic autogenerate failed without local PostgreSQL running"
  - "@vitejs/plugin-react@latest requires Vite 8, project uses Vite 6"
  - "Semgrep pip install clobbered backend dependencies"
  - "func.timezone() crashed on Neon PostgreSQL (production 500)"
  - "Enum case sensitivity in partial index WHERE clause"
  - "Rate limiter import name mismatch (shared_limiter vs limiter)"
  - "@fontsource fonts invisible when imported after Tailwind"
root_cause: "MUI's Material Design DNA fights cyberpunk aesthetic; no subject/session/dashboard APIs existed; toolchain assumptions from training data were stale"
severity: major-feature
resolution_time: "1 session (~6 hours active work)"
pr: "#25"
session_export: "~/.claude/exports/ai-study-architect/2026-03-14-session8-full-product-build-phases-neg1-0-1.txt"
compound_agents: 3
symptoms_count: 13
solutions_count: 11
mistakes_count: 12
meta_pattern: "User caught 9 of 12 mistakes -- AI as primary quality gate is unsustainable"
---

# Full Product Build: MUI to Tailwind v4 + New Backend APIs

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Symptoms (13)](#symptoms)
3. [Solutions (11)](#solutions)
4. [Mistakes and Prevention (12)](#mistakes-and-prevention)
5. [Meta-Pattern Analysis](#meta-pattern-analysis)
6. [Files Changed](#files-changed)
7. [Related Documents](#related-documents)

---

## Problem Statement

Study Architect was a functional MUI prototype with a light theme (Roboto font, `#f5f5f5` background, Material Design blue `#1976d2`) and only two features: chat interface with Socratic tutor and content upload/management. The target was a cyberpunk telemetry dashboard (void black `#050505`, neon chartreuse `#D4FF00`, cyan `#00F2FE`) with subject management, study session lifecycle tracking, real-time dashboard metrics, contribution heatmap, and a Zen-aesthetic focus session with Web Worker timer.

The gap between "working prototype" and "shippable product" was:
- The entire visual identity layer (MUI Material Design to cyberpunk telemetry)
- Three new backend API domains (subjects, sessions, dashboard)
- Database schema changes (new models, migrations, partial indexes)
- CI modernization (Node 20, semgrep isolation, updated action versions)

MUI's Material Design opinions (Roboto font assumption, elevation shadows, light-mode defaults, `#f5f5f5` backgrounds, 4px/8px spacing grid) are fundamentally incompatible with a cyberpunk telemetry aesthetic. Every neon glow, every JetBrains Mono data label, every sharp-cornered card with decorative corner markers requires fighting MUI's specificity via `sx` prop overrides and `!important` hacks. The Emotion CSS-in-JS runtime adds ~30-50KB overhead. Rethemeing MUI would cost MORE time than replacing it because the visual philosophies are irreconcilable.

---

## Symptoms

### S1: MUI visual identity incompatible with cyberpunk aesthetic

**Where**: Entire frontend (`frontend/src/`)
**Manifestation**: Every component needed `sx` overrides, `!important` hacks, and theme provider gymnastics to achieve dark-mode neon styling. Roboto font bled through everywhere. MUI elevation shadows created light-mode visual artifacts on dark backgrounds.

### S2: No backend APIs for subjects, sessions, or dashboard

**Where**: `backend/app/api/v1/`
**Manifestation**: Only auth, chat, content, and tutor endpoints existed. No way to track what a user is studying, for how long, or to aggregate metrics for a dashboard.

### S3: shadcn batch install silently created no files

**Where**: `frontend/` directory
**Manifestation**: Running `npx shadcn@latest add button card input dialog dropdown-menu tabs toast --yes` completed without errors but created zero component files. No error output, no partial results, no indication of failure. Only discovered when checking `frontend/src/components/ui/` and finding it empty.

### S4: husky init failed in monorepo

**Where**: `frontend/` directory
**Manifestation**: `npx husky init` from `frontend/` errored with ".git can't be found". The `.git` directory is at the repo root, not in the frontend subdirectory. Husky requires initialization from the git root.

### S5: CSP worker-src 'none' would silently block Web Worker in production

**Where**: `backend/app/core/security_headers.py` line 183
**Manifestation**: Caught by security review agent, NOT by runtime testing. The production CSP had `worker-src: 'none'` and `child-src: 'none'`, which would silently block the focus timer Web Worker with no visible error to the user. Development and staging already had `'self' blob:`. This was a showstopper that would have shipped to production undetected by standard testing.

### S6: StudySession schema int/UUID mismatch

**Where**: `backend/app/schemas/study_session.py`
**Manifestation**: `StudySessionResponse` had `id: int` and `user_id: int` but the database model uses `UUID(as_uuid=True)`. All existing tests passed because they never exercised UUID serialization. The mismatch would cause Pydantic validation errors on real API calls returning UUID values.

### S7: Alembic autogenerate failed without local PostgreSQL

**Where**: `backend/alembic/`
**Manifestation**: `alembic revision --autogenerate` failed because it needs an active database connection to diff models against schema. Local PostgreSQL was not running (Windows service off). The command fails silently or with a connection error depending on configuration.

### S8: @vitejs/plugin-react version conflict with Vite 6

**Where**: `frontend/package.json`
**Manifestation**: `npm install` with `@vitejs/plugin-react@latest` (6.0.1) failed with `ERESOLVE unable to resolve dependency tree` because version 6.0.1 requires `vite@^8.0.0` as a peer dependency. The project uses Vite 6.

### S9: Semgrep pip install clobbered backend dependencies

**Where**: `.github/workflows/deploy.yml`
**Manifestation**: CI deploy failed at test step. `pip install semgrep` in the same virtualenv as the backend replaced pydantic (2.9 to 2.12), starlette (0.35 to 0.52), and httpx (0.27 to 0.28). This broke FastAPI which requires starlette<0.36.

### S10: func.timezone() crashed on Neon PostgreSQL

**Where**: `backend/app/api/v1/dashboard.py`
**Manifestation**: Dashboard endpoint returned 500 Internal Server Error on production after deploy. Worked locally. SQLAlchemy's `func.timezone(user_tz, StudySession.actual_start)` behaved differently on Neon PostgreSQL, possibly due to NULL `actual_start` values from chat-created sessions.

### S11: Enum case sensitivity in partial index

**Where**: `backend/alembic/versions/942421c3cadb_add_subjects_table_and_session_fields.py`
**Manifestation**: Partial unique index `WHERE status IN ('in_progress', 'paused')` did not match database records because Python's `SessionStatus` enum stores values as their string representation, and the enum members are `IN_PROGRESS = "in_progress"` but stored through SQLAlchemy's Enum type which may preserve case differently. The index had to match the exact stored values.

### S12: Rate limiter import name mismatch

**Where**: `backend/app/api/v1/subjects.py`, `study_sessions.py`, `dashboard.py`
**Manifestation**: `ImportError: cannot import name 'shared_limiter' from 'app.core.rate_limiter'`. Three new routers used `shared_limiter` but the module exports `limiter`. This is a consequence of the Session 7 rate limiter consolidation which renamed the singleton.

### S13: @fontsource fonts invisible when imported after Tailwind

**Where**: `frontend/src/index.css`
**Manifestation**: Space Grotesk, JetBrains Mono, and Inter were not rendering. The browser was falling back to system fonts. CSS specification requires `@import` statements before all other rules. When Tailwind's `@import "tailwindcss"` came first, subsequent `@fontsource` imports were silently ignored in some browsers, or their styles were overridden by Tailwind's Preflight reset.

---

## Solutions

### Solution 1: Full Tailwind v4 Migration with Correct Ordering

**Symptom addressed**: S1 (MUI incompatibility), S8 (Vite plugin conflict)

**Why not retheme MUI**: Three approaches were evaluated. Heavy MUI retheme was "Material Design wearing a costume." Hybrid (Tailwind layout + MUI forms) meant two styling systems. Full Tailwind gives total pixel control, smaller bundle (~30-50KB less without Emotion), and Stitch `code.html` files were already Tailwind.

**Migration ordering** (CRITICAL -- discovered through deepening research):
1. Install Tailwind + shadcn + all new deps ALONGSIDE MUI (additive)
2. Rewrite all MUI components to Tailwind (auth forms, layout, pages)
3. Verify build passes with both installed
4. THEN `npm uninstall @mui/material @mui/icons-material @emotion/react @emotion/styled`

MUI was NOT fully removed in this session because ChatInterface.tsx (688 lines of complex streaming code) still uses MUI. Deferred to Phase 3 chat restyle.

**Vite plugin-react pinning**:
```bash
npm install -D vite@^6 @vitejs/plugin-react@^4.7.0 tailwindcss@latest @tailwindcss/vite
```
`@vitejs/plugin-react@^4.7.0` supports Vite 4-7. The `@latest` tag (6.0.1) requires Vite 8.

**vite.config.ts additions**:
```typescript
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [react(), tailwindcss()],
  worker: { format: 'es' },
  // ...
})
```

### Solution 2: CSS Import Ordering with layer(base) for Fonts

**Symptom addressed**: S13 (fonts invisible)

CSS specification requires `@import` statements before all other at-rules. Tailwind v4's `@import "tailwindcss"` includes Preflight (CSS reset), which resets font stacks. @fontsource imports must come FIRST and use `layer(base)` to ensure they survive Tailwind's layer ordering.

**Correct ordering** (from `frontend/src/index.css`):
```css
/* 1. @fontsource imports FIRST, in layer(base) */
@import "@fontsource/space-grotesk/400.css" layer(base);
@import "@fontsource/space-grotesk/700.css" layer(base);
@import "@fontsource/jetbrains-mono/400.css" layer(base);
@import "@fontsource/jetbrains-mono/500.css" layer(base);
@import "@fontsource/jetbrains-mono/700.css" layer(base);
@import "@fontsource/inter/400.css" layer(base);
@import "@fontsource/inter/500.css" layer(base);
@import "@fontsource/inter/600.css" layer(base);

/* 2. Tailwind import SECOND -- includes Preflight (CSS reset) */
@import "tailwindcss";

/* 3. Dark mode variant */
@custom-variant dark (&:is(.dark *));

/* 4. Design tokens consumed from DESIGN.md */
@theme {
  --color-primary: #D4FF00;
  --color-secondary: #00F2FE;
  --color-tertiary: #FF2D7B;
  --color-void: #050505;
  --color-surface: #0a0a0a;
  --color-raised: #121212;
  --color-border: #1f1f1f;
  --color-text-primary: #E0E0E0;
  --color-text-muted: #888888;
  --color-zen-primary: #4dffd2;
  --color-zen-bg: #0D0D0D;
  --font-display: 'Space Grotesk', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

Without `layer(base)`, the imports still work but are fragile to CSS engine differences. With it, font-face declarations are explicitly placed in the base layer where Tailwind expects foundational styles.

### Solution 3: shadcn/ui Manual Initialization and Individual Component Add

**Symptom addressed**: S3 (batch install silent failure)

The batch `add` command silently fails. The fix is two-part:

**Part 1**: Create `components.json` manually (or via `npx shadcn@latest init`):
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

**Part 2**: Add components one at a time:
```bash
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
# etc.
```

**Part 3**: Force-add gitignored files. The frontend `.gitignore` had blanket patterns matching `components.json` and `src/lib/`:
```bash
git add -f frontend/components.json frontend/src/lib/utils.ts
```

### Solution 4: Husky Monorepo Setup from Repo Root

**Symptom addressed**: S4 (husky init failure)

Husky requires `.git` in its working directory. In a monorepo with `frontend/` and `backend/` subdirectories, husky must be initialized from the repo root.

**Create root `package.json`**:
```json
{
  "private": true,
  "scripts": { "prepare": "husky" },
  "devDependencies": { "husky": "^9.1.7" }
}
```

**Initialize from repo root**:
```bash
npm install   # from repo root
npx husky init
```

**Pre-commit hook** (`.husky/pre-commit`):
```bash
cd frontend && npx lint-staged
```

### Solution 5: CSP worker-src Fix for Web Workers

**Symptom addressed**: S5 (CSP blocks Web Worker in production)

**Before** (`backend/app/core/security_headers.py`, production CSP):
```python
"worker-src": "'none'",
"child-src": "'none'",
```

**After**:
```python
"worker-src": "'self' blob:",
"child-src": "'self' blob:",
```

Development and staging already had `'self' blob:`. Only the production environment had `'none'`. The `blob:` source is required because Vite's worker bundling (with `worker: { format: 'es' }`) creates workers via blob URLs in production builds.

This was caught by the security review agent during `/plan_review`, not by runtime testing. It would have been a production showstopper with no user-visible error -- the timer would simply never start.

### Solution 6: StudySession Schema UUID Fix and Pydantic v2 Migration

**Symptom addressed**: S6 (int/UUID mismatch)

**Before**:
```python
class StudySessionResponse(BaseModel):
    id: int
    user_id: int
    class Config:
        from_attributes = True
```

**After** (`backend/app/schemas/study_session.py`):
```python
class StudySessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject_id: Optional[uuid.UUID] = None
    accumulated_seconds: int = 0
    status: Optional[str] = None
    # ... other fields ...
    model_config = ConfigDict(from_attributes=True)
```

Also added two new schemas:
```python
class StartSessionRequest(BaseModel):
    subject_id: Optional[uuid.UUID] = None
    study_mode: str = "practice"
    title: Optional[str] = None

class SessionStateResponse(BaseModel):
    id: uuid.UUID
    status: str
    accumulated_seconds: int
    duration_minutes: int
    subject_id: Optional[uuid.UUID] = None
    title: str
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
```

### Solution 7: Manual Alembic Migration for Partial Unique Index

**Symptom addressed**: S7 (autogenerate failure), S11 (enum case sensitivity)

Alembic `autogenerate` was not viable: (a) local PostgreSQL was off, (b) autogenerate does NOT detect partial unique indexes anyway. Migration written manually.

**Key migration sections**:
```python
# Subjects table
op.create_table('subjects',
    sa.Column('id', UUID(as_uuid=True), primary_key=True),
    sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('color', sa.String(7), nullable=False, server_default='#D4FF00'),
    sa.Column('weekly_goal_minutes', sa.Integer, nullable=False, server_default='300'),
    sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
    sa.UniqueConstraint('user_id', 'name', name='uq_subject_user_name'),
)

# Session fields
op.add_column('study_sessions', sa.Column('subject_id', UUID(as_uuid=True),
    sa.ForeignKey('subjects.id'), nullable=True))
op.add_column('study_sessions', sa.Column('accumulated_seconds', sa.Integer,
    nullable=False, server_default='0'))
op.add_column('study_sessions', sa.Column('last_resumed_at', sa.DateTime, nullable=True))

# Partial unique index -- enum values MUST match stored case
op.create_index(
    'idx_one_active_session_per_user', 'study_sessions', ['user_id'],
    unique=True,
    postgresql_where=sa.text("status IN ('IN_PROGRESS', 'PAUSED')"))

# Composite indexes for dashboard queries
op.create_index('idx_study_sessions_user_status_start',
    'study_sessions', ['user_id', 'status', sa.text('actual_start DESC')])
op.create_index('idx_study_sessions_user_subject_start',
    'study_sessions', ['user_id', 'subject_id', sa.text('actual_start DESC')])
```

**Starting local PostgreSQL** (Windows, from Git Bash without admin):
```bash
pg_ctl -D "C:/Program Files/PostgreSQL/17/data" start
```
Note: Windows PostgreSQL Service won't start from Bash tool, but `pg_ctl` works.

### Solution 8: Semgrep Isolation via pipx

**Symptom addressed**: S9 (semgrep clobbering deps)

**Before** (`.github/workflows/deploy.yml`):
```yaml
- run: pip install semgrep
- run: semgrep scan --config p/python-security backend/
```

**After**:
```yaml
- run: pipx install semgrep
- run: semgrep scan --config auto --include "*.py" backend/
```

Two fixes: (1) `pipx` installs semgrep in an isolated environment that cannot touch the app's virtualenv. (2) `--config auto` replaces the defunct `p/python-security` registry path that returned HTTP 404 (S10 from the Semgrep config 404).

### Solution 9: Dashboard 3-Query Pattern with Python Timezone Computation

**Symptom addressed**: S10 (func.timezone crash), S2 (no dashboard API)

**The wrong approach** (caused production 500):
```python
# DO NOT USE -- crashes on Neon PostgreSQL
func.timezone(user_tz, StudySession.actual_start)
```

**The correct approach** (`backend/app/api/v1/dashboard.py`):

Compute timezone boundaries in Python, pass UTC values to SQL WHERE clauses:
```python
user_tz = zoneinfo.ZoneInfo(current_user.timezone or "UTC")
now_local = datetime.now(user_tz)
today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

# Convert to UTC for WHERE clauses (preserves index usage per P1)
utc = zoneinfo.ZoneInfo("UTC")
today_start_utc = today_start_local.astimezone(utc)
```

Three focused queries instead of one monolithic query:
1. **28-day aggregation** grouped by `cast(actual_start, Date)` + `subject_id` -- covers today, week, heatmap, and subject breakdown in one scan
2. **Active session check** via partial index (instant) -- `status IN ('IN_PROGRESS', 'PAUSED')`
3. **Streak calculation** -- `distinct(cast(actual_start, Date))` ordered DESC, LIMIT 365

Streak algorithm counts consecutive days backwards from today:
```python
streak = 0
check_date = today_date
study_date_set = {row[0] for row in study_dates}
while check_date in study_date_set:
    streak += 1
    check_date -= timedelta(days=1)
```

### Solution 10: Stitch MCP Screen Editing with DESIGN.md Tokens

**Symptom addressed**: S1 (visual identity), Phase -1 design iteration

**Exact prompt structure used** (with `enhance-prompt` skill):
```
DESIGN SYSTEM (REQUIRED):
- Platform: Web, Desktop-first (1280-1440px max-width container)
- Background: Void Black (#050505)
- Surface: Raised Black (#0a0a0a) for cards, 1px borders in #1f1f1f
- Primary Accent: Neon Chartreuse (#D4FF00)
- Secondary Accent: Electric Cyan (#00F2FE)
- Danger: Hot Magenta (#FF2D7B)
- Headings: Space Grotesk, bold (700), UPPERCASE, tight tracking
- Data/Numbers: JetBrains Mono, medium (500)
- Body: Inter, regular (400)

REMOVE these elements: [specific gamification elements]
REPLACE [section] with: [specific mastery metrics with exact layout]
ADD [new element]: [detailed specification with color/typography/layout]
```

**Stitch MCP API pattern**:
```
list_screens(projectId) -> get screen IDs
edit_screens(projectId, selectedScreenIds, deviceType: "DESKTOP",
             modelId: "GEMINI_3_PRO", prompt: "...")
get_screen(projectId, screenId) -> download screenshot + HTML
```

Model ID: `GEMINI_3_PRO` (not GEMINI_3 or GEMINI_PRO -- exact Stitch model identifier).

**Screens edited**: Dashboard (heavy -- removed SysAdmin/XP/badges, added mastery metrics), Subject Detail (medium -- generic subjects, color-coded mastery bars), Active Focus (medium -- MCQ card, Zen aesthetic), Weekly Analytics (none -- copied from v2).

### Solution 11: Web Worker Timer with visx Heatmap

**Symptom addressed**: S5 (CSP for workers), dashboard visualization

**Web Worker timer** (`frontend/src/workers/timer.worker.ts`):

Uses `Date.now()` delta tracking (not increment counter) for accuracy:
```typescript
let startTime: number | null = null
let isRunning = false

function tick() {
  if (!isRunning || startTime === null) return
  const elapsed = Date.now() - startTime
  self.postMessage({ type: 'tick', elapsed })
  setTimeout(tick, 1000)  // NOT setInterval -- avoids drift accumulation
}
```

Key decisions:
- `setTimeout` recursion, not `setInterval` (avoids drift accumulation)
- 1000ms tick rate (displays HH:MM:SS, not milliseconds -- 10x fewer messages)
- `Date.now()` delta tracking (not simple counter) for accuracy across pause/resume
- `worker.terminate()` in `useEffect` cleanup

**Vite worker import**: `new URL('../workers/timer.worker.ts', import.meta.url)` with `{ type: 'module' }`. Requires `worker: { format: 'es' }` in vite.config.ts.

**Contribution heatmap** (`frontend/src/components/dashboard/ContributionHeatmap.tsx`):

Pure SVG implementation (visx was planned but a simpler custom SVG solution was used):
```typescript
function getCellColor(minutes: number): string {
  if (minutes === 0) return '#121212'
  if (minutes < 30) return '#1a4d4f'
  if (minutes < 60) return '#00a9b5'
  if (minutes < 120) return '#00d9e8'
  return '#00F2FE'
}
```

SVG glow filter applied ONLY to cells with 60+ minutes (performance P2 finding):
```tsx
<defs>
  <filter id="heatmap-glow">
    <feGaussianBlur stdDeviation="1.5" result="blur" />
    <feMerge>
      <feMergeNode in="blur" />
      <feMergeNode in="SourceGraphic" />
    </feMerge>
  </filter>
</defs>
<rect
  filter={cell.minutes >= 60 ? 'url(#heatmap-glow)' : undefined}
/>
```

Empty state: all 28 squares rendered in void color (`#121212` at 0.15 opacity) -- shows anticipation, matches GitHub contribution graph pattern.

---

## Mistakes and Prevention

### Mistake 1: Prematurely declaring agents dead

**What happened**: During `/deepen-plan`, checked task output files and found 0 bytes. Declared all 5 deepening agents "hit API rate limit" and "exhausted rate allowance."

**Reality**: 3 agents were still running (completed minutes later with full results). Only 1 genuinely failed (Cloudflare 403). The 0-byte files were output-in-progress, not failed.

**Who caught it**: User ("you're being too trigger-happy with declaring failure")

**Prevention**: Wait for task completion notification before declaring failure. Agents with 0 bytes may be in-progress, not failed. If you must check early, wait at least 3-5 minutes.

**Rule created**: `~/.claude/projects/.../memory/feedback_agent_behavior.md`

### Mistake 2: Inventing explanations without evidence

**What happened**: Attributed agent failures to "exhausted rate allowance" -- a concept that doesn't exist for Anthropic API subagents. Cloudflare 403 is a transient bot-detection challenge, not a rate limit.

**Who caught it**: User (challenged the "rate allowance" concept)

**Prevention**: Diagnose before explaining. "I don't know why" is better than a fabricated explanation. Distinguish between: (a) Cloudflare 403 = transient bot-detection, (b) HTTP 429 = actual rate limit, (c) 0-byte output = still running.

### Mistake 3: Not researching v0 MCP existence

**What happened**: Said "No v0 MCP, skill, or plugin exists in our toolset" based only on checking installed tools. Didn't search the web.

**Who caught it**: User ("I meant even online, not just my config, why were you so myopic in your search?")

**Prevention**: Always search online (WebSearch, GitHub, npm) for tools/MCPs before asserting they don't exist. Local toolset is not the universe. A v0 MCP community server did exist (hellolucky/v0-mcp with 4 tools).

**Rule created**: `~/.claude/projects/.../memory/feedback_research_thoroughness.md`

### Mistake 4: Deferring Figma without justification

**What happened**: Initially deferred Figma to "post-MVP" with generic "1-2 week setup" estimate from research. This was effort avoidance disguised as pragmatism.

**Who caught it**: User ("why not everything from the start if we eventually gonna upgrade later anyways?")

**Prevention**: Before deferring anything to "later" or "Phase 2," verify the deferral is justified by architecture (adding it NOW would make things worse), not by effort avoidance. Claude doesn't feel effort.

**Outcome**: Re-evaluated. Actual setup for the project was 4-7 hours (tokens already defined). Simplicity review later made a valid counter-argument for solo dev. Final decision was defer, but the initial deferral reasoning was wrong.

**Rule created**: `~/.claude/projects/.../memory/feedback_no_deferring_without_cause.md`

### Mistake 5: Not researching product decisions

**What happened**: Brainstorm defined "mastery %" as `concepts_mastered / total_concepts` without researching how MathAcademy/Anki/Khan actually calculate mastery. Existing 12K+ words of MathAcademy research in the quantelect repo went unread.

**Who caught it**: User ("did you check the quantelect research?")

**Prevention**: Always check existing project research (quantelect repo, memory files, prior session exports) before inventing product definitions. For learning algorithm design specifically: SM-2, FSRS, MathAcademy, Khan Missions all have published analyses.

**Rule created**: `~/.claude/projects/.../memory/feedback_research_product_decisions.md`

### Mistake 6: Not applying reconciliation fixes inline

**What happened**: Architecture review found 14 contradictions between plan sections. Created a "Review Reconciliation" header section declaring which version was authoritative. But the task bodies still contained the wrong versions -- creating copy-paste traps.

**Who caught it**: User (noticed task bodies still had wrong instructions during implementation)

**Prevention**: Apply fixes INLINE to the task bodies that will be copy-pasted during implementation. A reconciliation header is useful as an index, but insufficient as the sole fix location. The implementer reads task bodies, not reconciliation headers.

Specific contradictions that needed inline fixes: `sendBeacon` -> `fetch({keepalive})`, 100ms setInterval -> 1000ms setTimeout, framer-motion in npm install -> remove, single query dashboard -> 3-query pattern, `get_current_active_user` -> `get_current_user`.

**Rule created**: `~/.claude/projects/.../memory/feedback_inline_fixes.md`

### Mistake 7: Cached model IDs from training data

**What happened**: Used `claude-sonnet-4-6-20250514` model ID from training data. This was stale -- actual current model ID is different.

**Who caught it**: User ("from Anthropic's official sources, not pulled outta your ass")

**Prevention**: NEVER use values from training data for volatile identifiers. Always verify from official sources (navigate to provider's model docs page). Store the verification instruction ("check this URL"), not the value.

**Rule created**: `~/.claude/rules/verify-volatile-data.md` (global scope)

### Mistake 8: Skipping code review before deploy

**What happened**: Pushed to production without running `/workflows:review`. The dashboard `func.timezone()` 500 was only caught by post-deploy Playwright UI testing.

**Who caught it**: Production (500 error on deployed dashboard endpoint)

**Prevention**: Always run `/workflows:review` before deploy. Local tests and CI are insufficient -- they don't test against the production database driver (Neon PostgreSQL behaves differently from local PostgreSQL for some SQLAlchemy functions).

### Mistake 9: Premature "session complete" claims (6 occurrences)

**What happened**: Declared work "ready to export" or "session complete" at least 6 times while actionable items remained:
- After Phase 0 frontend foundation (backend not started)
- After backend models (no router tests)
- After CI fixes (deploy not verified)
- After deploy (production 500 not tested)
- After fixing production 500 (compound doc not written)
- After compound doc (review findings not integrated)

**Who caught it**: User (each time, by pointing out remaining work)

**Prevention**: Before any "session complete" or "ready to export" claim:
1. Re-read the task list -- are all tasks done?
2. Re-read MEMORY.md entries edited this session -- do they match final state?
3. Check: did you identify anything during the session that you haven't done yet?
4. Claude doesn't feel fatigue. If work remains, keep working.

### Mistake 10: Deleting memory file instead of updating

**What happened**: When correcting outdated information in a memory file, deleted the entire file and recreated it instead of editing in place. This lost git history and made the change unauditable.

**Who caught it**: User (noticed file deletion in git status)

**Prevention**: Use Edit tool to update existing files. Only use Write for new files. Git history on edited files preserves the evolution of understanding. Deletion + recreation looks like a new file.

### Mistake 11: Running compound skill too late

**What happened**: The `/compound` skill (which produces this document) was run as an afterthought near session end, after context was already heavy from 6 hours of work. This meant the compound document was less thorough and required a second pass with dedicated agents.

**Who caught it**: User (requested the 3-agent compound pass that produced this integrated version)

**Prevention**: Run `/compound` or take notes for compound documentation DURING the session, not after. Key moments to capture: after each bug fix, after each review finding resolution, after each mistake correction. Accumulating raw material throughout is easier than reconstructing from degraded context.

### Mistake 12: Insufficient verification of CSS import ordering

**What happened**: Initial Tailwind setup had `@import "tailwindcss"` before `@fontsource` imports. Fonts appeared to work in dev (hot reload covers some ordering issues) but would fail in production builds.

**Who caught it**: Discovered during deepening research on Tailwind v4 best practices (research agent, not user or runtime)

**Prevention**: For any CSS framework migration, research the exact import ordering requirements FIRST. Tailwind v4 has specific requirements about `@import` ordering and `@layer` placement that differ from v3. Test with a production build (`npm run build && npm run preview`), not just dev server.

---

## Meta-Pattern Analysis

### The User as Primary Quality Gate is Unsustainable

Of the 12 mistakes documented above, the **user caught 9** of them:

| # | Mistake | Caught by |
|---|---------|-----------|
| 1 | Premature agent death declaration | User |
| 2 | Inventing explanations | User |
| 3 | Not researching v0 MCP | User |
| 4 | Deferring Figma without cause | User |
| 5 | Not researching product decisions | User |
| 6 | Not applying reconciliation inline | User |
| 7 | Cached model IDs | User |
| 8 | Skipping code review | Production (500 error) |
| 9 | Premature "session complete" (6x) | User |
| 10 | Deleting memory file | User |
| 11 | Compound skill too late | User |
| 12 | CSS import ordering | Research agent |

Only 2 were caught by automated systems (production error, research agent). The remaining 1 was self-caught through research.

**This means**: The user is functioning as the primary quality gate for AI behavior. This is the inverse of what compound engineering promises. The human should be making creative and strategic decisions, not catching basic process failures.

**Categories of user-caught mistakes**:
- **Effort avoidance** (4, 9, 11): Deferring work, declaring done prematurely, leaving documentation to the end
- **Insufficient research** (3, 5, 7): Not searching broadly enough, not checking existing artifacts, using stale cached data
- **Process shortcuts** (6, 8, 10): Skipping review steps, surface-level fixes, destructive operations
- **Confabulation** (1, 2): Making up explanations, declaring states without evidence

**Structural fixes needed** (beyond per-mistake prevention):
1. **Pre-completion checklist** enforced by the compound engineering workflow itself, not by user vigilance
2. **Research-first gates** that block implementation until sources are verified (not just "remember to research")
3. **Session progress tracking** with explicit "remaining work" visible at all times (task list is mandatory, not optional)
4. **Compound documentation as continuous accumulation**, not end-of-session reconstruction

The meta-lesson: creating rules for each mistake is necessary but insufficient. The rules themselves need enforcement mechanisms that don't rely on the user remembering to check. The session discipline rules in `~/.claude/rules/session-discipline.md` exist because of exactly this session, but rules only work if the agent follows them proactively.

---

## Files Changed

### Backend (new)
- `backend/app/models/subject.py` -- Subject model with UUID, color auto-assignment (8-color palette), UniqueConstraint(user_id, name)
- `backend/app/schemas/subject.py` -- Pydantic schemas with field validators, Unicode normalization (NFKC)
- `backend/app/api/v1/subjects.py` -- CRUD router with rate limiting, ownership verification, max 50 subjects per user
- `backend/app/api/v1/study_sessions.py` -- Session lifecycle router (start/pause/resume/stop/active/history) with 409 on invalid transitions
- `backend/app/api/v1/dashboard.py` -- 3-query dashboard summary endpoint with Python timezone computation
- `backend/alembic/versions/942421c3cadb_add_subjects_table_and_session_fields.py` -- Manual migration with partial unique index + 2 composite indexes

### Backend (modified)
- `backend/app/models/user.py` -- Added `subjects` relationship
- `backend/app/models/study_session.py` -- Added `subject_id`, `accumulated_seconds`, `last_resumed_at`, `subject` relationship
- `backend/app/schemas/study_session.py` -- Fixed int/UUID mismatch, added `StartSessionRequest`, `SessionStateResponse`, Pydantic v2 `model_config`
- `backend/app/api/v1/api.py` -- Registered subjects, sessions, dashboard routers
- `backend/app/core/csrf.py` -- Added `/api/v1/subjects/`, `/api/v1/sessions/`, `/api/v1/dashboard` to JWT exempt list
- `backend/app/core/security_headers.py` -- Fixed `worker-src: 'self' blob:'` (was `'none'` in production)
- `backend/alembic/env.py` -- Added Subject model import

### Frontend (new)
- `frontend/src/app/layout/AppShell.tsx` -- Dark layout wrapper with Outlet
- `frontend/src/app/layout/TopNav.tsx` -- Tailwind nav (replaces MUI AppBar)
- `frontend/src/pages/DashboardPage.tsx` -- Dashboard with hero metrics, heatmap, empty states
- `frontend/src/pages/StudyPage.tsx` -- Study/chat page wrapper
- `frontend/src/pages/ContentPage.tsx` -- Content management wrapper
- `frontend/src/pages/FocusPage.tsx` -- Zen-aesthetic focus session with timer
- `frontend/src/components/dashboard/HeroMetrics.tsx` -- 4 metric cards with CSS `@starting-style` staggered reveal
- `frontend/src/components/dashboard/SubjectList.tsx` -- Subject progress bars with color-coded fills
- `frontend/src/components/dashboard/ContributionHeatmap.tsx` -- SVG 28-day heatmap with glow filters on 60+ min cells
- `frontend/src/components/dashboard/StartFocusCTA.tsx` -- Full-width chartreuse CTA
- `frontend/src/hooks/useTimer.ts` -- Web Worker timer hook with Zustand integration
- `frontend/src/workers/timer.worker.ts` -- Date.now()-based background timer with setTimeout recursion
- `frontend/src/lib/utils.ts` -- shadcn `cn()` utility (clsx + tailwind-merge)
- `frontend/src/index.css` -- Complete Tailwind v4 `@theme` with all design tokens from DESIGN.md
- `frontend/components.json` -- shadcn/ui configuration
- `frontend/prettier.config.js` -- Prettier with tailwindcss plugin

### Frontend (modified)
- `frontend/src/App.tsx` -- Rewritten from 359 lines MUI to 49 lines Tailwind
- `frontend/src/components/auth/LoginForm.tsx` -- MUI to Tailwind+shadcn
- `frontend/src/components/auth/RegisterForm.tsx` -- MUI to Tailwind+shadcn
- `frontend/src/components/auth/ProtectedRoute.tsx` -- MUI to Tailwind
- `frontend/vite.config.ts` -- Added `@tailwindcss/vite`, `worker: { format: 'es' }`, pinned `@vitejs/plugin-react@^4.7.0`
- `frontend/package.json` -- New deps, lint-staged config

### Design
- `design/stitch/v3-evolved/dashboard/` -- Edited screen (PNG + HTML)
- `design/stitch/v3-evolved/subject-detail/` -- Edited screen (PNG + HTML)
- `design/stitch/v3-evolved/active-focus/` -- Edited screen (PNG + HTML)
- `design/stitch/v3-evolved/weekly-analytics/` -- Copied from v2 (PNG + HTML)
- `design/stitch/v3-evolved/README.md` -- What changed from v2

### CI
- `.github/workflows/deploy.yml` -- checkout@v6, setup-python@v6, setup-node@v6, Node 18->20, semgrep to pipx
- `.github/workflows/staging.yml` -- checkout@v6, setup-python@v6, setup-node@v6, Node 18->20

### Project Configuration
- `.claude/rules/stitch-implementation.md` -- Stitch to React implementation workflow
- `package.json` (root) -- Minimal, for husky in monorepo
- `.husky/pre-commit` -- `cd frontend && npx lint-staged`

---

## Related Documents

- **Brainstorm**: `docs/brainstorms/2026-03-13-mvp-frontend-brainstorm.md` (486 lines)
- **Plan**: `docs/plans/2026-03-14-001-feat-full-product-build-phases-neg1-0-1-plan.md` (1129 lines)
- **SM-2 Research**: `~/.claude/projects/.../memory/sm2-fire-mastery-research.md`
- **CI Fixes**: `~/.claude/projects/.../memory/session8-ci-and-deploy-fixes.md`
- **Agent Behavior Feedback**: `~/.claude/projects/.../memory/feedback_agent_behavior.md`
- **Research Thoroughness Feedback**: `~/.claude/projects/.../memory/feedback_research_thoroughness.md`
- **No Deferring Feedback**: `~/.claude/projects/.../memory/feedback_no_deferring_without_cause.md`
- **Product Research Feedback**: `~/.claude/projects/.../memory/feedback_research_product_decisions.md`
- **Inline Fixes Feedback**: `~/.claude/projects/.../memory/feedback_inline_fixes.md`
- **Official Sources Feedback**: `~/.claude/projects/.../memory/feedback_official_sources_only.md`
- **Session Export**: `~/.claude/exports/ai-study-architect/2026-03-14-session8-full-product-build-phases-neg1-0-1.txt` (12,579 lines)
- **Design System**: `design/DESIGN.md`
- **PRD**: `design/PRD.md`

### Compound Engineering Workflow Used

```
/brainstorming (8m) -> /workflows:plan (5m) -> /deepen-plan (6 agents, 15m)
-> /plan_review (3 agents, 10m) -> /workflows:work (~3h)
-> Production UI test (Playwright) -> CI fix iteration
-> /compound (initial) -> 3-agent compound pass (this document)
```

### Research Consumed

- 12+ background research agents (Tailwind v4, visx, headless UI, Stitch vs Figma, Storybook/v0/Chromatic, SM-2/FIRe, GitHub Actions, semgrep)
- 2 Context7 MCP queries (visx docs, shadcn/ui docs)
- 6 skill evaluations (react-components, ui-from-mockup, frontend-design, enhance-prompt, figma:implement-design, figma:create-design-system-rules)
- 4 Stitch screen renders analyzed
- 2 quantelect research files read (24K+ words MathAcademy analysis)
- Playwright MCP production UI testing (8+ page navigations)
- 3 compound analysis agents (context analyzer, solution extractor, prevention strategist)
