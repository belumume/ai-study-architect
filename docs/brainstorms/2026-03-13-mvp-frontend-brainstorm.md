---
date: 2026-03-13
topic: mvp-frontend-rebuild
---

# MVP Frontend: The Objective Best

## What We're Building

A complete frontend rebuild of Study Architect that replaces the current MUI light-mode scaffold with a production-grade, dark-mode telemetry dashboard. The target experience: a serious study instrument that surfaces insight, tracks mastery, and disappears during focus — not a gamified toy.

**Core metaphor**: Mission control for your brain. Bloomberg Terminal meets Strava meets Anki.

**Five screens**:
1. **Dashboard** — daily mission control (what to study, how much done, where you stand)
2. **Study Session** — AI chat with Socratic tutor (existing feature, restyled)
3. **Active Focus** — distraction-free timer with live session data (Zen aesthetic)
4. **Subject Detail** — drill-down into one subject's mastery and history
5. **Analytics** — weekly/monthly patterns, peak performance, knowledge gaps

**One aesthetic system with two modes**:
- **Analytics Pro** (Dashboard, Subject Detail, Analytics): cyberpunk telemetry — void black, neon chartreuse + cyan, data-dense, JetBrains Mono everywhere
- **Zen Study** (Active Focus): calm, minimal, softer palette (#4dffd2 teal, #B4A7FF lavender), the interface disappears so the student can focus

This dual aesthetic IS the product feature. When reviewing, you want information density. When studying, you want absence of distraction.

---

## Why This Approach

### The Existing Frontend Is a Prototype
Current state: MUI light theme, Roboto, `#f5f5f5` background, placeholder pages for Home/Practice, functional chat + content upload. ~688 lines of ChatInterface with streaming, scroll management, abort control. Good engineering, wrong visual identity.

The gap between "MUI blue Roboto on light gray" and "void-black cyberpunk neon" is not a retheme — it's a visual identity transplant. Attempting to override MUI's Material Design opinions to achieve this aesthetic would cost more than replacing it, and the result would never match.

### Greenfield Permission Applied
Nothing pre-existing is sacred — not the MUI components, not the Stitch mockup content, not the routing, not the state management. Every choice made from first principles for what's objectively best in March 2026.

The Stitch v2 renders are INSPIRATION for the aesthetic (the visual language is strong and differentiated). But the information architecture evolves:
- **Less game**: No SysAdmin levels, no arbitrary XP points, no "ENGAGE" buttons, no collectible badges
- **More insight**: Mastery percentage (evidence-based), knowledge gap identification, retention velocity, study recommendations, actual learning metrics
- **Streaks stay**: Proven behavior driver (Duolingo research). Simple, honest, no inflation.
- **New Stitch screens can be created** if the information architecture demands layouts the current mockups don't serve

---

## Key Decisions

### 1. Full Tailwind CSS v4 + shadcn/ui (replaces MUI + Emotion)

**Rationale**: DESIGN.md already defines a Tailwind config. Stitch code.html files are pure Tailwind implementations. Tailwind v4 uses CSS-first configuration with native CSS variables — the design tokens map directly. shadcn/ui provides accessible Radix-based primitives (Dialog, Select, Tabs, Form, Input, Toast, DropdownMenu) that we own and style completely.

MUI's Material Design DNA actively fights this aesthetic. Every neon glow, every JetBrains Mono label, every sharp-cornered card = a specificity war. Emotion runtime adds ~30-50KB. shadcn/ui + Tailwind is lighter, more customizable, and aligns with the design system.

**Research confirmed (March 2026)**: Tailwind v4 stable since Jan 2025, 3.78x faster builds. `@tailwindcss/vite` is the official Vite approach. shadcn/ui fully supports Tailwind v4. shadcn now offers Base UI (MUI team, v1.0 stable Dec 2025) as alternative backend to Radix — useful fallback if Radix maintenance degrades (slowed post-WorkOS acquisition). We start with Radix (more examples/community) knowing Base UI is a drop-in swap.

**What gets removed**: `@mui/material`, `@mui/icons-material`, `@emotion/react`, `@emotion/styled`
**What gets added**: See full Technology Stack section below (tailwindcss v4, shadcn/ui, visx, ~~Framer Motion~~ [REMOVED: YAGNI — CSS handles animations, see Resolved Questions], Zustand, CVA, @fontsource, lucide-react, react-markdown, prettier-plugin-tailwindcss, and more)

### 2. visx for Data Visualization (not Recharts, not Chart.js)

**Rationale**: The charts in this product are highly custom — neon glows, void-black backgrounds, 1px strokes, specific color stops, JetBrains Mono labels, animated drawing. No charting library produces this out of the box.

visx (Airbnb) gives D3-level control with React components. Each chart type is a composable primitive: `Bar`, `LinePath`, `Pie`, `Group`, scales, axes. The `XYChart` high-level API has `buildChartTheme` for consistent dark styling. SVG elements accept `filter` and `style` props for glow effects. Total control, zero fighting.

Recharts is opinionated. Chart.js is canvas-based (no SVG control). Nivo is beautiful but imposes its own aesthetic. visx is the only library that says "here are the primitives, build whatever you want."

**Research confirmed (March 2026)**: visx ~15KB bundle (vs Recharts 50-70KB, Nivo 150KB+). Native SVG `<feGaussianBlur>` + `<feMerge>` for neon glow effects. `buildChartTheme` API for consistent dark styling. No Emotion dependency needed — visx SVG elements accept standard props; Tailwind handles wrapper styling.

**Charts needed**: contribution heatmap, velocity ring (SVG arc), bar chart, line chart, donut chart, focus degradation graph

### 3. Desktop-First (not mobile-first)

**Rationale**:
- Target audience (competitive academics) studies on laptops
- v2 Stitch designs are 1280-1440px desktop layouts
- Data-dense dashboards are fundamentally desktop experiences
- The design system already defines both breakpoints (390px mobile, 1280px desktop) — mobile adaptation follows desktop implementation
- Active Focus is the only screen that works equally well on mobile (centered timer)

### 4. Full Scope, No Fakes — Design for Real Data

**Rationale**: Designing a "time tracking dashboard" now and redesigning into a "mastery dashboard" later is building twice. Instead: design every screen for the FULL product scope. Build backend and frontend together per feature. Each phase ships real functionality with real data — never placeholder metrics.

**What this means concretely:**
- "Mastery %" = real concept-level mastery from AI-extracted concepts + practice attempts. Not `time_spent / weekly_goal`.
- "Knowledge gaps" = real gap identification from concept extraction. Not "subjects you haven't studied."
- "Study recommendations" = real SM-2 spaced repetition scheduling. Not "study what you neglected."
- "Active Focus" = real practice questions generated from extracted concepts. Not just a timer.
- Dashboard sections appear progressively as backend features land. No section displays fake data — it simply doesn't render until real data exists.

### 5. Information Architecture: Insight Over Game

**Rationale**: For the stated audience (medical students, law students, competitive academics who "treat studying like elite athletic training"), the correct gamification level is Anki/MathAcademy, not Duolingo:

| Element | Keep? | Why |
|---------|-------|-----|
| Mastery % per concept | Yes | Real measurement: AI concept extraction + practice accuracy |
| Streaks | Yes | Proven behavior driver, honest |
| Study time tracking | Yes | Core feature, foundational data |
| Knowledge gaps | Yes | Real: concepts extracted but not yet mastered |
| Spaced repetition schedule | Yes | SM-2 algorithm on concept-level mastery data |
| Practice questions | Yes | AI-generated from extracted concepts, graded |
| XP points | No | Proxy metric, doesn't measure learning |
| Levels/titles (SysAdmin Lvl.07) | No | Patronizing for serious students |
| Collectible badges | Defer | Can add later if users want them |
| "ENGAGE" action buttons | No | Unclear affordance, game-like |

The dashboard answers five questions at a glance — ALL with real data:
1. "What should I study right now?" — SM-2 scheduler: concepts due for review, weakest concepts first
2. "How much have I studied today?" — time telemetry with daily/weekly context
3. "Am I actually learning?" — concept-level mastery % from practice attempts
4. "Where are my weak spots?" — concepts extracted but scoring below mastery threshold
5. "Am I on track?" — goal progress + retention curve trajectory

### 6. Chat Gets Markdown Rendering

**Rationale**: Known issue — chat currently renders `**bold**` as literal asterisks. The Socratic tutor outputs markdown (code blocks, bold, lists, headers). Adding `react-markdown` + `remark-gfm` + `rehype-highlight` is essential for the chat to function as designed.

### 7. Timer Uses Web Workers

**Rationale**: `setInterval` in the main thread drifts over time (browser throttles background tabs). A Web Worker maintains accurate timing even when the tab is inactive. For a study timer where accuracy matters (session logs, analytics), this is the right approach.

### 8. Keep React Router v6 (not TanStack Router)

**Rationale**: 5 routes. The routing layer is not the bottleneck. React Router v6 is known, stable, sufficient. TanStack Router's type-safe params and file-based routing are nice but add migration complexity during a visual rewrite for minimal gain. YAGNI.

---

## Technology Stack

### Core
| Category | Choice | Replaces |
|----------|--------|----------|
| Framework | React 18 + TypeScript 5.5 (strict mode) | (keep) |
| Build | Vite 6 | Vite 5 |
| Styling | Tailwind CSS v4 + CSS variables | MUI + Emotion |
| UI Primitives | shadcn/ui (Radix-based, copy-paste) | MUI components |
| Component Variants | CVA (Class Variance Authority) | (new — shadcn uses internally) |
| Icons | Lucide React | MUI Icons |
| Charts | visx (D3 + React) | (new) |
| Animation | Framer Motion | (new) |
| Fonts | @fontsource (self-hosted, version-pinned) | Google Fonts CDN |

### State & Data
| Category | Choice | Notes |
|----------|--------|-------|
| Server state | TanStack Query v5 | Keep — excellent |
| Client state | Zustand | Timer, session, theme, UI state |
| Forms | React Hook Form + Zod + @hookform/resolvers | Keep RHF, add Zod + resolver bridge |
| Routing | React Router v6 | Keep |

### Content & UX
| Category | Choice | Notes |
|----------|--------|-------|
| Chat rendering | react-markdown + remark-gfm + rehype-highlight | Known gap — fixes literal asterisks |
| Timer | Web Worker | Accurate timing even in background tabs |
| Date handling | date-fns | Keep |
| File upload | react-dropzone | Keep |

### Quality & DX
| Category | Choice | Notes |
|----------|--------|-------|
| Tailwind class sorting | prettier-plugin-tailwindcss | Official Tailwind Labs, requires `tailwindStylesheet` for v4 |
| Tailwind linting | @poupe/eslint-plugin-tailwindcss | Full v4 support (original plugin stuck in rewrite) |
| Pre-commit hooks | husky + lint-staged | Frontend linting on commit (ruff handles Python) |
| Visual regression | Playwright `toHaveScreenshot()` | Free, built into existing devDeps |
| Performance gating | Lighthouse CI (GitHub Actions) | Free, gates on every commit |
| Accessibility | axe + Playwright `checkA11y` | Critical for dark theme contrast ratios |

### Design Token Flow
```
Figma Variables (source of truth)
  → export to CSS custom properties
    → Tailwind @theme block (consumer)
      → components use Tailwind classes
```

### Design Tokens (Tailwind v4 CSS, consumed from Figma Variables)
```css
@theme {
  /* Core palette */
  --color-primary: #D4FF00;
  --color-secondary: #00F2FE;
  --color-tertiary: #FF2D7B;
  --color-accent: #FF00FF;
  --color-gold: #FFD700;

  /* Surfaces */
  --color-void: #050505;
  --color-surface: #0a0a0a;
  --color-raised: #121212;
  --color-border: #1f1f1f;

  /* Text */
  --color-text-primary: #E0E0E0;
  --color-text-muted: #888888;

  /* Zen palette (focus session) */
  --color-zen-primary: #4dffd2;
  --color-zen-secondary: #B4A7FF;
  --color-zen-bg: #0D0D0D;

  /* Typography */
  --font-display: 'Space Grotesk', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

---

## Backend: Full Scope

### What Exists
- StudySession model with timing fields (actual_start, actual_end, duration_minutes, focus_score)
- Content processing pipeline (upload, extract text, store)
- Chat endpoints with Claude API streaming (POST /chat, GET /history, GET /session/{id})
- Content CRUD (upload, list, get, delete, search)
- Auth (register, login, refresh, logout, me)
- Tutor (chat, study-plan, progress, adapt-difficulty)
- AI service manager (Claude primary, OpenAI fallback)

### What's Needed — Grouped by Phase

**Phase 1: Subjects + Sessions (enables Dashboard + Focus Session)**
- Subject CRUD — `POST /subjects`, `GET /subjects`, `GET /subjects/{id}`, `PATCH /subjects/{id}`, `DELETE /subjects/{id}` (with weekly goals, color assignment)
- Study session lifecycle — `POST /sessions/start`, `PATCH /sessions/{id}/pause`, `PATCH /sessions/{id}/resume`, `PATCH /sessions/{id}/stop`
- Dashboard summary — `GET /dashboard` (today's time, streak, subject breakdown)
- New schema: `subjects` table (name, color, weekly_goal_minutes, user_id)

**Phase 2: Concept Extraction (enables real mastery data)**
- Concept extraction pipeline — when content is uploaded, Claude API extracts atomic concepts + dependencies
- New schema: `concepts` table (name, subject_id, content_id, dependencies JSON), `user_concept_mastery` table (user_id, concept_id, mastery_score, last_reviewed, next_review)
- Endpoints: `GET /subjects/{id}/concepts`, `GET /concepts/{id}/mastery`
- Batch job: extract concepts from existing uploaded content

**Phase 4: Practice Generation (enables real Active Focus)**
- Practice question generation — Claude API generates questions from extracted concepts
- Attempt tracking — record user answers, grade (AI-graded for open-ended, auto for MCQ)
- New schema: `practice_questions` table, `practice_attempts` table
- Endpoints: `POST /practice/generate`, `POST /practice/{id}/attempt`, `GET /practice/history`

**Phase 5: SM-2 Scheduling + Analytics (enables recommendations + analytics)**
- SM-2 algorithm — calculate next review date per concept based on mastery + attempt history
- Analytics aggregation — `GET /analytics/daily`, `GET /analytics/weekly`, `GET /analytics/heatmap`, `GET /analytics/subject/{id}/velocity`, `GET /analytics/retention-curve`
- Recommendation engine — `GET /dashboard/recommendations` (concepts due for review, weakest first)
- No new schema — queries over existing concept mastery + attempt data

**Infrastructure note**: Concept extraction and practice generation use the SAME Claude API infrastructure as the existing Socratic tutor — different prompts, same service manager. This is not a new system — it's new endpoints on existing infrastructure.

---

## Design-to-Code Pipeline

### Tools & Skills (Research-Validated March 2026)

| Stage | Tool | What It Does |
|---|---|---|
| **Generate screens** | Stitch MCP (`generate_screen_from_text`) | Text prompt → design + Tailwind HTML. Free, 350/month. Gemini 3 model. |
| **Edit screens** | Stitch MCP (`edit_screens`) | Modify existing screens (remove gamification, add mastery metrics) |
| **Explore variants** | Stitch MCP (`generate_variants`) | Generate 1-5 variants with REFINE/EXPLORE/REIMAGINE creative range |
| **Optimize prompts** | `enhance-prompt` skill | Structures prompts with DESIGN.md tokens for consistent Stitch output |
| **Import to Figma** | Stitch native export | Stitch exports to Figma natively. Import for refinement + token governance. [DEFERRED: plan review decision — tokens-as-code sufficient for solo dev] |
| **Refine + manage tokens** | Figma + Figma Variables | Source of truth for design tokens. Visual refinement of layouts. [DEFERRED: plan review decision] |
| **Extract design data** | Figma MCP (`get_design_context`, `get_screenshot`) | Structured data: exact px, token refs, component hierarchy, auto layout [DEFERRED: plan review decision] |
| **Implement from Figma** | `figma:implement-design` skill | Structured workflow: fetch context → screenshot → implement → validate [DEFERRED: plan review decision] |
| **Generate design rules** | `figma:create-design-system-rules` skill | Generates CLAUDE.md rules for consistent Figma-to-code implementation [DEFERRED: plan review decision] |
| **Convert to React** | `react-components` skill | Stitch HTML → modular React + TypeScript + hooks + data layer |
| **Automate iteration** | `stitch-loop` skill | Autonomous design→code→screenshot→compare→iterate (optional, Phase 1-4) |
| **Validate visuals** | Playwright `toHaveScreenshot()` | Free visual regression testing, built into existing devDeps |
| **Gate performance** | Lighthouse CI (GitHub Actions) | Performance gating on every commit (free) |
| **Audit accessibility** | axe + Playwright `checkA11y` | Dark theme contrast ratios are critical (free) |

### Why Stitch + Figma (Complementary, ~~Both From Start~~ Figma Deferred)

**Stitch MCP**: Rapid design generation from text. MCP integrated — zero context switching. Text → design + Tailwind HTML in seconds. Best for ideation and initial screen creation.

**Figma MCP**: Design refinement, token governance (Figma Variables as source of truth), pixel-perfect implementation via `get_design_context` (structured data: exact px, token refs, component hierarchy, auto layout). Best for precision and consistency. ~~Integrated from Phase 0.~~ [DEFERRED: plan review decision — DESIGN.md tokens-as-code via Tailwind @theme is the direct path for solo dev. Figma plugs in later if team grows.]

**Pipeline**: Stitch generates → exports to Figma → Figma refines + manages tokens → Figma MCP extracts structured data → `react-components` converts to React → customize. Both tools MCP-integrated, zero platform switching.

**Setup cost**: ~4-7 hours (DESIGN.md tokens already defined, Stitch exports to Figma natively). Not the generic "1-2 weeks" — we've already done the design system work.

**v0 (Vercel)**: Official API and community MCP exist. Generates shadcn/ui + Tailwind React directly. But with Figma in the pipeline, Figma MCP's structured data is objectively more accurate than v0's screenshot inference. Genuinely superseded, not arbitrarily dismissed. v0 SDK noted as available fallback if pipeline friction warrants it.

**Risk mitigation**: Stitch is a Google Labs experiment (launched May 2025). Google kills Labs projects. Having Figma integrated from day 1 means Stitch disappearing would not break our pipeline — Figma continues independently as the durable long-term design infrastructure.

### Evaluated and Skipped (with rationale)

| Tool | Verdict | Why |
|---|---|---|
| v0 (Vercel) | Superseded | Official API exists, community MCP exists (hellolucky/v0-mcp), but with Figma in pipeline, Figma MCP's structured data (`get_design_context`) is objectively more accurate than v0's screenshot inference. v0 SDK noted as available fallback. |
| Storybook | Skip for MVP | Research-confirmed: value at 50+ components or 3+ devs. Hot reload + direct inspection sufficient for 20-30 components. |
| Chromatic | Skip | $179-399/month. Playwright `toHaveScreenshot()` is free and sufficient. Percy free tier as upgrade path. |
| Vercel MCP (official) | Note as available | Deployment management (logs, project context), not design-to-code. We deploy via git push. Useful for deploy debugging, not blocking. |
| `ui-from-mockup` skill | Superseded | Defaults to MUI + mobile-first — conflicts with our decisions |
| `design-md` skill | Superseded | DESIGN.md already comprehensive |
| `frontend-design` skill | Insight extracted | Generic design guidance superseded by DESIGN.md. One insight adopted: orchestrated page load animations. |

### Motion Design (from `frontend-design` skill)

Add orchestrated page load animations beyond DESIGN.md's data-focused animations:
- **Dashboard load**: Staggered metric card reveals with `animation-delay` (200ms between cards)
- **Chart drawing**: SVG `stroke-dashoffset` animations fire sequentially as sections enter viewport
- **Page transitions**: Framer Motion `AnimatePresence` for route changes
- **Philosophy**: "One well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions"

---

## Build Order

### Phase -1: Design Iteration (before coding)
- Use `enhance-prompt` to craft Stitch prompts with DESIGN.md tokens + FULL scope IA
- Use Stitch MCP `edit_screens` on Dashboard (heavy: remove SysAdmin/XP/badges, add mastery %/knowledge gaps/SM-2 recommendations/concept progress)
- Use Stitch MCP `edit_screens` on Subject Detail (medium: concept map with real mastery data, practice history)
- Use Stitch MCP `edit_screens` on Active Focus (medium: real practice questions, not just timer)
- Analytics: usable as-is with minor label updates
- Review generated screens, iterate with `generate_variants` if needed
- Export all screens from Stitch to Figma (native export)
- Import into Figma project, begin token mapping to Figma Variables
- Download final HTML + screenshots for implementation reference

### Phase 0: Foundation (setup, no features)
- Tailwind v4 + Vite 6 setup with `@tailwindcss/vite` plugin
- shadcn/ui initialization with custom dark theme (Radix backend)
- @fontsource self-hosted fonts (Space Grotesk, JetBrains Mono, Inter)
- Figma setup (completing Phase -1 import): finalize Figma Variables from DESIGN.md tokens, build basic component library, run `figma:create-design-system-rules` to generate CLAUDE.md implementation rules
- Design tokens: Figma Variables (source) → CSS custom properties → Tailwind `@theme` (consumer)
- Quality tooling: prettier-plugin-tailwindcss, @poupe/eslint-plugin-tailwindcss, husky + lint-staged
- TypeScript strict mode verified
- Layout shell (top nav, responsive container, routing)
- Dark mode as default (not toggle — dark IS the identity)
- Lighthouse CI + Playwright visual test baseline + axe integration
- Create `.claude/rules/stitch-implementation.md` (structured workflow)

### Phase 1: Subjects + Time Tracking (Backend + Frontend)
**Backend**: Subject CRUD, study session lifecycle, dashboard summary endpoint, `subjects` table
**Frontend**: Dashboard (hero metrics: today's time, streak, active subjects, subject progress bars, contribution heatmap, "Start Focus" CTA) + basic Focus Session (timer, subject selector, pause/resume)
**Result**: Real subjects, real time tracking, real streaks. Dashboard sections that depend on concept data (mastery %, recommendations) don't render yet — they appear when data exists.

### Phase 2: Concept Extraction + Mastery (Backend + Frontend)
**Backend**: Concept extraction pipeline (Claude API on uploaded content), `concepts` + `user_concept_mastery` tables, batch extraction on existing content
**Frontend**: Subject Detail page (concept map with real mastery data, 7-day velocity chart, telemetry log). Dashboard mastery section lights up.
**Result**: Upload materials → AI extracts concepts → real mastery % per concept appears on dashboard and subject detail.

### Phase 3: Chat Restyle + Markdown (Frontend only)
**Backend**: Existing chat backend works — no changes needed
**Frontend**: ChatInterface restyled in cyberpunk aesthetic, react-markdown integration (code blocks, bold, lists, headers), dark theme message bubbles
**Result**: Socratic tutor with proper rendering. Can be done in parallel with Phase 2 backend.

### Phase 4: Practice Generation + Real Focus (Backend + Frontend)
**Backend**: Practice question generation endpoint (Claude API from extracted concepts), attempt tracking, grading (AI for open-ended, auto for MCQ), `practice_questions` + `practice_attempts` tables
**Frontend**: Active Focus upgraded from timer-only to real practice (questions from concepts, accuracy tracking, session summary with performance data)
**Result**: Focus session = actual learning, not just a clock. Mastery % updates from practice attempts.

### Phase 5: SM-2 Scheduling + Analytics (Backend + Frontend)
**Backend**: SM-2 algorithm (next review date per concept), recommendation engine, analytics aggregation queries, retention curve calculation
**Frontend**: Analytics page (focus degradation, subject allocation donut, peak performance, retention curves). Dashboard recommendations section lights up ("study this next" = SM-2 due concepts, weakest first).
**Result**: Complete product. Every metric is real. Every recommendation is algorithmic. Every screen displays actual learning data.

### Progressive Enhancement Pattern
Frontend sections render conditionally based on data availability:
```tsx
{concepts.length > 0 && <MasterySection concepts={concepts} />}
{recommendations.length > 0 && <RecommendationList items={recommendations} />}
{retentionData && <RetentionCurve data={retentionData} />}
```
No fake data. No placeholder metrics. Sections appear when their data is real.

---

## Product Decisions (Research-Grounded)

### Mastery % Definition
**Source**: MathAcademy research (quantelect repo), SM-2 algorithm literature

Per-concept mastery based on **spaced repetition count** (MathAcademy model), not binary pass/fail:
- Each concept tracks: `repetition_count`, `ease_factor`, `last_reviewed`, `next_review`, `consecutive_correct`
- **Mastered**: `consecutive_correct >= 2` (MathAcademy's gate: two correct in a row)
- **Subject mastery %**: `concepts_mastered / total_concepts_in_subject`
- **Scheduling**: SM-2 algorithm — `interval = prev_interval × ease_factor`, ease adjusted by quality rating (0-5)
- **Future consideration**: FSRS (Free Spaced Repetition Scheduler, Anki 23.10+) — ML-trained on 700M reviews from 20K users. 20-30% fewer daily reviews while maintaining retention. Potentially better than SM-2 for our use case. Evaluate during Phase 5.
- **Long-term (Phase 5+)**: FIRe-inspired implicit repetition — practicing advanced concepts gives fractional credit to prerequisites. Requires mature knowledge graph. Deferred because FIRe is complex (20+ page academic paper) and requires deep prerequisite mapping.
- **Full research**: See `~/.claude/projects/.../memory/sm2-fire-mastery-research.md` for SM-2 formulas, FSRS comparison, FIRe algorithm details, mastery thresholds, and grading tiers.

NOT time-based. NOT a proxy. Real mastery = demonstrated understanding through practice.

### Mastery Gates: Steering, Not Blocking
**Source**: Khan Academy Missions failure (2014-2020, retired because rigid gates felt punitive)

Critical design decision: mastery gates are **recommendations, not locks**:
- Algorithm recommends what to study next (weakest concepts, due reviews)
- Users CAN access any content freely — not gated behind prerequisites
- Dashboard prominently shows "recommended next" but doesn't prevent exploration
- Gamification makes progress feel rewarding (streaks, mastery rings filling) not restrictive
- This directly mitigates the Khan Missions failure mode while preserving MathAcademy's mastery benefits

### First-Run Experience
**Source**: MathAcademy diagnostic assessment pattern

**Progressive feature disclosure** (Duolingo model, adapted):
- **Day 0**: Upload content, ask one question, get Socratic response = immediate value. Designed empty states guide to first action.
- **Day 1**: Suggest first practice question (low barrier). Introduce Focus Session.
- **Day 3**: Introduce mastery tracking (after habit formation, not before).
- **Week 1**: Surface spaced repetition schedule + analytics (after student has data to analyze).
- Features exist from Phase 2+, but new users are introduced progressively — not all at once.

**Technical flow (behind the progressive UX)**:
1. Sign up → Dashboard with designed empty states + "Create Subject" / "Upload Materials" cards
2. Content upload → AI extracts concepts using SVO structure (30-60 seconds)
3. Optional diagnostic quiz on extracted concepts → map initial "knowledge frontier"
4. Dashboard populates progressively as data accumulates

### Concept Extraction Risk
**Source**: Quantelect MathAcademy research — "programming prerequisites are murkier than math"

Known risk: AI concept extraction from diverse academic content may be imperfect.
- Math has hard prerequisites (algebra → calculus). CS has soft prerequisites (many valid learning paths).
- **Best practice (research-confirmed)**: Extract as atomic SVO (Subject-Verb-Object) learning objectives, not vague topic names. "Calculate derivative using chain rule" not "understand calculus." SVO reduces ambiguity.
- **Relation identification**: Extract prerequisite, similarity, and containment relations to build knowledge graph edges.
- **Mitigation**: User can review/edit extracted concepts. Manual concept creation as fallback.
- **Start narrow**: CS subjects with clearer hierarchies (data structures, algorithms) before broader subjects.
- **Empirical testing**: Phase 2 must include quality evaluation of extraction on real student content.
- **Full research**: See `~/.claude/projects/.../memory/sm2-fire-mastery-research.md` for extraction methods and research citations.

### Auto-Grading Approach
**Source**: EDM 2025 — 96.77% accuracy, ~$0.005/submission, <5s latency

Multi-modal assessment (not just code execution):
- MCQ (auto-graded, instant)
- Code submissions (AI-graded, 96.77% accuracy, ~$0.005 each)
- Concept questions (AI-graded open-ended, lower confidence → flag uncertain grades)
- If AI confidence < threshold, mark as "needs review" rather than asserting correctness
- Cost at scale: 100K submissions/day = ~$500/day — manageable with existing AI budget

### Chat + Focus Session Relationship
Separate screens, connected by state:
- **Chat** = open-ended Socratic dialogue (existing feature). Exploratory learning.
- **Focus Session** = structured practice on specific concepts (new feature). Active recall.
- During Focus, the AI generates practice questions from extracted concepts — dedicated practice UI, not the chat interface.
- Both create StudySession records. Both feed mastery data.
- Users switch freely between exploratory (Chat) and structured (Focus).

### Study Session vs Focus Session
"Study Session" = database model (tracks all study activity). "Focus Session" = UI mode (timer + practice questions). A Focus Session creates a StudySession record with `study_mode = PRACTICE`. Chat creates StudySession records with `study_mode = DISCUSSION`. Analytics aggregates both.

### When Is It "Shipped"?
Phase 1 = minimum shippable (subjects, time tracking, dashboard, basic focus timer). Each subsequent phase adds a complete feature with real data. No single "MVP done" moment — each phase ships real value. Phase 2 (concept extraction) is the first phase where mastery data becomes real.

---

## Resolved Questions

1. **New Stitch designs needed?** YES — Phase -1 added. Edit Dashboard (heavy) and Subject Detail (light) via Stitch MCP before coding. Focus Session and Analytics usable as-is.

2. **MUI replacement strategy?** Full Tailwind v4 + shadcn/ui. No retheme, no hybrid. Clean replacement.

3. **Design tool pipeline?** Stitch for design generation. Figma deferred (plan review decision: tokens-as-code via DESIGN.md → Tailwind @theme is the direct path; Figma adds a sync layer that doesn't add information for a solo dev). Figma plugs in later if team grows. See plan reconciliation.

4. **v0/Storybook/Chromatic?** All skipped with research-backed rationale. Playwright visual tests cover the quality gap for free.

5. **Build architecture?** Full scope, interleaved backend + frontend per feature. No fake data. Progressive enhancement — sections render when their data is real.

6. **First-run experience?** Designed empty states that guide (not broken-looking empty screens). "Add Subject" + "Upload Materials" cards.

7. **Chat vs Focus relationship?** Separate screens. Chat = exploratory Socratic dialogue. Focus = structured concept practice. Both create StudySession records, both feed mastery.

## Remaining Open Questions

1. ~~Authentication UI restyle~~ — DONE in Phase 0.4 (session 8).

2. **Content management restyle** — Upload/list/selector need dark treatment. Can reuse component patterns from dashboard.

3. **Mobile navigation timing** — Desktop uses top nav. Mobile uses bottom nav (per DESIGN.md). Recommendation: after Phase 1 desktop is solid, generate mobile Stitch variants.

4. **Mastery threshold** — What score constitutes "mastered"? 90% (MathAcademy standard)? 80%? Configurable per user? Decision can be made during Phase 2 implementation.

5. **Concept extraction quality** — How good is Claude at extracting atomic concepts from diverse academic content? Needs empirical testing in Phase 2. Fallback: user-defined concepts.

---

## Next Steps

1. Execute Phase -1: Generate evolved Stitch screens for FULL scope (Dashboard, Subject Detail, Active Focus)
2. `/workflows:plan` for Phase 0 + Phase 1 implementation details
