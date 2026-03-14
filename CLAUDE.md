# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Study Architect** by Quantelect — Mastery-based AI study companion that proves you learned it. Currently focused on CS education as beachhead market. Uses Claude API (primary) and OpenAI (fallback).

**Live**: https://aistudyarchitect.com
**Core Philosophy**: "Build cognitive strength, not cognitive debt"
**Strategic Direction**: See [docs/direction/NEW_DIRECTION_2025.md](docs/direction/NEW_DIRECTION_2025.md)
**Design Direction**: Analytics Pro "cyberpunk telemetry" aesthetic — see [design/PRD.md](design/PRD.md) and [design/DESIGN.md](design/DESIGN.md)
**Related Repos**: `quantelect/` (company/pitch), `cs50/` (course history)

## Important Development Rules

### NO EMOJIS in Code or Terminal Output
- **NEVER use emojis** in Python scripts, test files, or any code that will be executed
- **NEVER use emojis** in terminal output, log messages, or print statements
- **NEVER use emojis** in git commit messages (except the robot emoji for Claude attribution)
- Windows terminals and Python encoding often fail with Unicode emojis (UnicodeEncodeError)
- Use ASCII alternatives: [PASS], [FAIL], [WARN], SUCCESS:, ERROR:, etc.
- This prevents encoding errors and ensures cross-platform compatibility

## Common Development Commands

### Backend Development
```bash
cd backend
# Local development
python -m venv venv
venv\Scripts\activate                          # Windows
source venv/bin/activate                       # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload                  # Start dev server (port 8000)

# Testing
pytest tests/                                   # Run all tests
pytest tests/test_auth.py                      # Run specific test file
pytest -v -s                                    # Verbose output with print statements
venv\Scripts\python.exe tests/scripts/quick_socratic_test.py  # Test Socratic mode (Windows)

# Code quality
ruff check app/                                # Lint code
ruff check app/ --fix                          # Auto-fix linting issues
mypy app/                                      # Type checking
coverage run -m pytest                         # Run tests with coverage
coverage report                                # Show coverage report

# Database
alembic upgrade head                           # Run migrations
alembic revision --autogenerate -m "message"  # Create new migration
```

### Frontend Development
```bash
cd frontend
# Setup and development
npm install                                    # Install dependencies
npm run dev                                    # Start dev server (port 5173)

# Testing and validation
npm test                                       # Run tests with Vitest
npm run test:ui                               # Run tests with UI
npm run test:coverage                         # Generate coverage report
npm run typecheck                             # Check TypeScript types
npm run lint                                  # Lint code with ESLint

# Production build
npm run build                                 # Build for production (tsc && vite build)
npm run preview                               # Preview production build

# Tailwind / styling
# Tailwind v4 uses @tailwindcss/vite plugin — no tailwind.config needed
# Design tokens defined in src/index.css @theme block
# Class sorting: prettier-plugin-tailwindcss (auto on save/commit)
# shadcn/ui components: npx shadcn@latest add <component>
```

### E2E Testing
```bash
cd frontend
npx playwright test                           # Run all E2E tests
npx playwright test --ui                      # Run with UI mode
npx playwright test streaming-scroll          # Run specific test
```

### Test Coverage & Quality Checks
```bash
# Backend test coverage
cd backend
coverage run -m pytest                        # Run tests with coverage tracking
coverage report                                # Display coverage report
coverage html                                  # Generate HTML coverage report
coverage report --fail-under=80               # Fail if coverage < 80%

# Frontend test coverage
cd frontend
npm run test:coverage                         # Generate coverage report
npm run test:coverage -- --reporter=html      # HTML coverage report

# Full quality check (backend)
cd backend
ruff check app/ && mypy app/ && pytest tests/ -v

# Full quality check (frontend)
cd frontend
npm run lint && npm run typecheck && npm test
```

### Environment Validation
```bash
# Check all required services are running
cd backend
python -c "
import sys
import socket

def check_port(port, service):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    if result == 0:
        print(f'[OK] {service} on port {port}')
        return True
    else:
        print(f'[FAIL] {service} on port {port} - not running')
        return False

# Check PostgreSQL
check_port(5432, 'PostgreSQL') or check_port(5433, 'PostgreSQL (Windows)')

# Check Redis
check_port(6379, 'Redis')

print('\nChecking Python dependencies...')
try:
    import fastapi
    import sqlalchemy
    import anthropic
    print('[OK] Core Python dependencies installed')
except ImportError as e:
    print(f'[FAIL] Missing dependency: {e}')
    sys.exit(1)
"

# Check frontend dependencies
cd frontend
node -e "
try {
  require('react');
  require('axios');
  console.log('[OK] Core frontend dependencies installed');
} catch (e) {
  console.log('[FAIL] Missing dependency:', e.message);
  process.exit(1);
}
"

# Verify environment variables
cd backend
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = ['DATABASE_URL', 'JWT_SECRET_KEY']
optional = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']

print('Checking required environment variables...')
for var in required:
    if os.getenv(var):
        print(f'[OK] {var}')
    else:
        print(f'[FAIL] {var} - REQUIRED')

print('\nChecking optional environment variables...')
for var in optional:
    if os.getenv(var):
        print(f'[OK] {var}')
    else:
        print(f'[WARN] {var} - Optional but recommended')
"
```

## High-Level Architecture

### Mastery-Based Learning System
**Current Implementation** (as of March 2026):
- Lead Tutor Agent - Provides Socratic questioning and explanations [IMPLEMENTED]
- File upload and content processing [IMPLEMENTED]
- Chat interface with streaming responses [IMPLEMENTED]
- Multi-provider AI integration (Claude primary, OpenAI fallback) [IMPLEMENTED]
- User authentication with JWT (RS256) [IMPLEMENTED]
- PostgreSQL database with session management [IMPLEMENTED]
- Subject CRUD with color assignment [IMPLEMENTED]
- Study session lifecycle (start/pause/resume/stop) [IMPLEMENTED]
- Dashboard summary with hero metrics, subject breakdown, heatmap data [IMPLEMENTED]
- Analytics Pro dashboard UI with Tailwind v4 + shadcn/ui [IMPLEMENTED]
- Focus timer with Web Worker [IMPLEMENTED]

**Phase 2** (next — see [docs/direction/NEW_DIRECTION_2025.md](docs/direction/NEW_DIRECTION_2025.md)):
1. **Knowledge Graph Extractor** - Extract atomic concepts and dependencies
2. **Practice Problem Generator** - Auto-graded programming exercises
3. **Mastery Tracker** - 90%+ gates before concept unlock
4. **Spaced Repetition Scheduler** - SM-2 algorithm
5. **Retention Analyzer** - Long-term learning measurement

### Backend Architecture (FastAPI)

**Directory Structure:**
```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── dependencies.py        # Shared dependency injection
│   │   └── v1/
│   │       ├── api.py            # Main router — includes all sub-routers
│   │       ├── auth.py           # Authentication endpoints
│   │       ├── chat.py           # Chat/conversation endpoints
│   │       ├── tutor.py          # Tutor agent endpoints
│   │       ├── csrf.py           # CSRF token endpoints
│   │       ├── admin.py          # Admin endpoints
│   │       ├── admin_security.py # Security admin endpoints
│   │       ├── agents.py         # Agent management endpoints
│   │       ├── content.py        # Content upload/management endpoints
│   │       ├── subjects.py       # Subject CRUD endpoints
│   │       ├── study_sessions.py # Session lifecycle (start/pause/resume/stop)
│   │       ├── dashboard.py      # Dashboard summary endpoint
│   │       ├── websocket.py      # WebSocket support
│   │       └── endpoints/
│   │           └── backup.py     # Backup management
│   ├── agents/
│   │   ├── base.py              # Base agent class [IMPLEMENTED]
│   │   └── lead_tutor.py        # Socratic questioning agent [IMPLEMENTED]
│   ├── core/
│   │   ├── config.py            # Configuration management
│   │   ├── security.py          # JWT, password hashing
│   │   ├── database.py          # Database connections
│   │   ├── csrf.py              # CSRF protection
│   │   ├── cache.py             # Upstash Redis caching (with _NoOpCache fallback)
│   │   ├── agent_manager.py     # Agent orchestration
│   │   ├── rsa_keys.py          # RSA key management for JWT
│   │   ├── security_headers.py  # Security headers middleware
│   │   ├── exceptions.py        # Custom exception handlers
│   │   └── upstash_cache.py     # Upstash Redis integration
│   ├── models/
│   │   ├── user.py             # User accounts [IMPLEMENTED]
│   │   ├── content.py          # Uploaded materials [IMPLEMENTED]
│   │   ├── study_session.py    # Learning sessions with lifecycle [IMPLEMENTED]
│   │   ├── subject.py          # Study subjects with color [IMPLEMENTED]
│   │   ├── practice.py         # Practice problems [IMPLEMENTED]
│   │   ├── chat_message.py     # Chat messages (schema exists)
│   │   └── concept.py          # Concepts (schema exists, Phase 2)
│   ├── schemas/
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── content.py          # Content schemas
│   │   ├── study_session.py    # Session schemas (with lifecycle states)
│   │   ├── subject.py          # Subject schemas
│   │   ├── concept.py          # Concept schemas (Phase 2)
│   │   └── agents.py           # Agent request/response schemas
│   └── services/
│       ├── ai_service_manager.py      # AI service selection (Claude -> OpenAI) [IMPLEMENTED]
│       ├── claude_service.py          # Anthropic Claude integration [IMPLEMENTED]
│       ├── openai_fallback.py         # OpenAI fallback service [IMPLEMENTED]
│       ├── content_processor.py       # File processing pipeline [IMPLEMENTED]
│       ├── vision_processor.py        # Image/vision processing [IMPLEMENTED]
│       └── ai/                        # AI service abstractions
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── e2e/                   # End-to-end tests
│   └── scripts/               # Test scripts
└── alembic/                   # Database migrations
    └── versions/              # Migration files
```

**Core Components:**
- `app/main.py` - FastAPI application with comprehensive middleware stack
- `app/api/v1/api.py` - Main router aggregating all sub-routers (11 routers)
- `app/agents/` - Agent implementations with Redis caching for state management
- `app/services/claude_service.py` - Claude API integration with streaming support
- `app/services/ai_service_manager.py` - Intelligent AI service selection and fallback
- `app/core/security.py` - JWT authentication with RS256 algorithm
- `app/core/csrf.py` - CSRF protection with strategic exemptions
- `app/core/cache.py` - Upstash Redis caching with _NoOpCache fallback
- `app/models/` - SQLAlchemy models for users, content, sessions, subjects, and practice

**Key Design Patterns:**
- Dependency injection for database sessions and authentication
- Service layer pattern for AI integrations
- Repository pattern for data access
- Middleware pipeline for cross-cutting concerns
- Streaming responses for real-time AI interactions
- Automatic fallback strategy for AI services
- Session state machine (in_progress/paused/completed/abandoned) with atomic transitions

### Frontend Architecture (React + TypeScript + Tailwind v4)

**Directory Structure:**
```
frontend/
├── src/
│   ├── app/
│   │   └── layout/
│   │       ├── AppShell.tsx       # Main layout (TopNav + Outlet + footer)
│   │       ├── TopNav.tsx         # Navigation bar
│   │       └── index.ts          # Layout barrel export
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx      # Login component (MUI — Phase 3 restyle)
│   │   │   ├── RegisterForm.tsx   # Registration component (MUI — Phase 3 restyle)
│   │   │   ├── ProtectedRoute.tsx # Route protection + GuestRoute
│   │   │   └── index.ts
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx  # Real-time chat with streaming (MUI — Phase 3 restyle)
│   │   │   └── index.ts
│   │   ├── content/
│   │   │   ├── ContentUpload.tsx  # File upload with drag-and-drop (MUI — Phase 3 restyle)
│   │   │   ├── ContentList.tsx    # Display uploaded content (MUI — Phase 3 restyle)
│   │   │   ├── ContentSelector.tsx # Content selection UI (MUI — Phase 3 restyle)
│   │   │   └── index.ts
│   │   ├── dashboard/
│   │   │   ├── HeroMetrics.tsx    # Today's time, mastery index, streak, subjects
│   │   │   ├── SubjectList.tsx    # Subject cards with progress
│   │   │   ├── ContributionHeatmap.tsx # 28-day study heatmap (visx)
│   │   │   ├── StartFocusCTA.tsx  # "Initiate Focus" call-to-action
│   │   │   └── index.ts
│   │   ├── ui/                    # shadcn/ui primitives (Radix-based)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── input.tsx
│   │   │   ├── sonner.tsx         # Toast notifications
│   │   │   └── tabs.tsx
│   │   └── ErrorBoundary.tsx      # Global error boundary
│   ├── config/
│   │   └── sentry.ts             # Sentry error tracking config
│   ├── contexts/
│   │   └── AuthContext.tsx        # Global authentication state
│   ├── hooks/
│   │   └── useTimer.ts           # Focus timer hook (Web Worker)
│   ├── lib/
│   │   └── utils.ts              # cn() utility (clsx + tailwind-merge)
│   ├── pages/
│   │   ├── DashboardPage.tsx     # Dashboard route (/ )
│   │   ├── StudyPage.tsx         # Study/chat route (/study)
│   │   ├── FocusPage.tsx         # Focus timer route (/focus)
│   │   ├── ContentPage.tsx       # Content management route (/content)
│   │   └── index.ts             # Page barrel export
│   ├── services/
│   │   ├── api.ts                 # Axios client with interceptors
│   │   ├── auth.service.ts        # Authentication service
│   │   └── tokenStorage.ts        # Token management
│   ├── test/
│   │   ├── setup.ts              # Test setup (Vitest)
│   │   ├── mocks.ts              # Mock utilities
│   │   └── test-utils.tsx        # Custom render with providers
│   ├── utils/
│   │   └── errorUtils.ts         # Error formatting utilities
│   ├── workers/
│   │   └── timer.worker.ts       # Web Worker for focus timer (1s ticks)
│   ├── App.tsx                    # Root routes (auth, app shell, pages)
│   ├── main.tsx                   # Application entry point
│   └── index.css                  # Design tokens (@theme), Tailwind import, glow utilities
├── components.json                # shadcn/ui configuration (Radix, Lucide icons)
├── tsconfig.json                  # TypeScript config with path aliases (@/*)
├── vite.config.ts                 # Vite 6 + React + @tailwindcss/vite plugin
├── public/                        # Static assets
├── tests/                         # Frontend tests
│   └── e2e/                      # Playwright E2E tests
└── dist/                          # Build output (gitignored)
```

**Routing:**
- `/login`, `/register` — Auth pages (GuestRoute, no shell)
- `/` — Dashboard (ProtectedRoute, AppShell)
- `/study` — Study/chat page (ProtectedRoute, AppShell)
- `/focus` — Focus timer page (ProtectedRoute, AppShell)
- `/content` — Content management (ProtectedRoute, AppShell)
- `*` — Redirects to `/`

**UI Framework (Dual System — Migration In Progress):**
- **New components (dashboard, layout, focus, ui/)**: Tailwind v4 + shadcn/ui (Radix primitives) + Lucide icons
- **Legacy components (chat, content, auth forms)**: MUI + Emotion — Phase 3 removal pending
- `src/index.css` — Design tokens in `@theme` block (void black, chartreuse, cyan, zen palette)
- `src/lib/utils.ts` — `cn()` helper (clsx + tailwind-merge) for conditional classes
- `components.json` — shadcn/ui config (aliases, icon library, CSS variables)
- Path aliases: `@/` -> `src/`, `@components/`, `@hooks/`, `@services/`, `@types/`, `@utils/`

**State Management:**
- React Query (@tanstack/react-query) for server state and caching
- Zustand for client state (timer, focus session, UI state)
- Context API for global auth state
- Local state for component-specific data

**Charts & Visualization:**
- visx (@visx/heatmap, @visx/scale, @visx/responsive, etc.) for all data visualization
- SVG-based with neon glow filters (feGaussianBlur + feMerge)
- Custom color scales matching design tokens

**Typography (self-hosted via @fontsource):**
- Display/headings: Space Grotesk (font-display)
- Body text: Inter (font-body)
- Data/numbers/code: JetBrains Mono (font-mono)

### Database Architecture

**PostgreSQL 17** with SQLAlchemy ORM:

**Current Tables:**
- `users` - Authentication and profiles
- `content` - Uploaded study materials with extracted text
- `study_sessions` - Learning sessions with lifecycle states (in_progress/paused/completed/abandoned), accumulated_seconds, last_resumed_at
- `subjects` - Study subjects with color assignment and user ownership
- `practice_problems` - Generated exercises with difficulty levels
- `chat_messages` - Conversation history with context (schema exists, full implementation pending)
- `concepts` - Atomic learning concepts (schema exists, Phase 2)

**Phase 2 (not in MVP scope):**
- `concept_dependencies` - Prerequisite relationships between concepts
- `user_attempts` - Student problem-solving attempts
- `mastery_status` - Per-concept mastery tracking
- `spaced_repetition_schedule` - Review scheduling (SM-2 algorithm)

### AI Integration Architecture

**Multi-Provider Strategy:**
1. **Claude API** (Primary) - Superior educational performance via Anthropic
2. **OpenAI API** (Fallback) - Automatic failover for reliability
3. **Direct SDK calls** - Anthropic + OpenAI SDKs (LangChain removed March 2026)

**Key Features:**
- Server-sent events (SSE) for streaming responses
- Token counting and usage tracking
- Context window management
- Prompt template system for consistency
- Intelligent service selection with automatic fallback
- Runtime API key validation (not import-time)

**Service Manager Flow:**
```
Request -> AI Service Manager
         |
    Claude Available?
         |-- Yes -> Claude Service -> Stream Response
         +-- No -> OpenAI Service -> Stream Response
```

### Security Verification
```bash
# Check JWT configuration
cd backend
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('JWT Configuration:')
print(f'Algorithm: {os.getenv(\"JWT_ALGORITHM\", \"RS256\")}')
print(f'Access Token Expiry: {os.getenv(\"JWT_ACCESS_TOKEN_EXPIRE_MINUTES\", \"30\")} minutes')

# Check if RSA keys exist
import os.path
if os.path.exists('keys/private.pem') and os.path.exists('keys/public.pem'):
    print('[OK] RSA keys found')
else:
    print('[WARN] RSA keys not found - using HS256 fallback')
"

# Verify CSRF protection
grep -r "CSRFProtect\|csrf_protect" backend/app/core/csrf.py && echo "[OK] CSRF protection enabled"

# Check for hardcoded secrets
cd backend
echo "Checking for hardcoded secrets..."
! grep -r "sk-[a-zA-Z0-9]" --exclude-dir=venv --exclude-dir=.git app/ && echo "[OK] No hardcoded API keys found"

# Security headers check
grep -A 10 "security_headers" backend/app/main.py && echo "[OK] Security headers middleware configured"

# Test authentication on local server (requires server running)
# curl -s http://localhost:8000/api/v1/users/me | grep -q "Not authenticated" && echo "[OK] Protected endpoints require auth"
```

## Platform-Specific Considerations

### Windows Development
- PostgreSQL runs on port 5433 (not standard 5432)
- Use `venv\Scripts\python.exe` for virtual environment
- Line endings: `.gitattributes` not currently present (was removed during migration)
- Database passwords with special chars need `quote_plus()` encoding
- May need to uncomment `python-magic-bin` in requirements.txt for file processing

### Cloudflare Containers
- Backend runs in CF Container (Docker, basic instance: 1/4 vCPU, 1 GiB)
- Worker routes /api/* to Container (singleton Durable Objects pattern)
- Scale-to-zero: container sleeps after 5 min idle, ~2-5s cold start
- Database: Neon PostgreSQL (serverless, auto-suspend)
- Storage: R2 (S3-compatible, file uploads + backups)
- Cache: Upstash Redis (REST API)
- Deploy: `cd worker && npx wrangler deploy`

### Vercel Frontend Hosting
- SPA routing handled by CF Worker (proxies all non-API routes to Vercel). No `vercel.json` in repo — direct Vercel access may need SPA rewrites if accessed outside CF Worker.
- Automatic deployments from GitHub
- Custom domain: aistudyarchitect.com
- Environment variables managed via Vercel dashboard

### Cloudflare Worker Routing
- Routes https://aistudyarchitect.com/api/* to backend (CF Container)
- MUST NOT strip /api prefix - backend expects full paths
- Returns 404 for /api/docs, /api/openapi.json, /api/redoc (security)
- Handles CORS for cross-origin requests

## Critical Reminders

### Development Workflow
- **Mastery-based focus** - Building for measurable learning outcomes, not agent count
- **Daily dev sessions** - See docs/planning/DAILY_DEV_PLAN.md for incremental progress
- **Strategic direction** - See docs/direction/NEW_DIRECTION_2025.md for current focus
- **Documentation** - See docs/README.md for organized doc navigation
- **Build plan** - See docs/plans/2026-03-14-001-feat-full-product-build-phases-neg1-0-1-plan.md for implementation plan

### Database & Backend
- **Neon for migrations** - Use direct (non-pooled) connection for `alembic upgrade head`
- **Port 5432 on Windows** - Local PostgreSQL for development
- **NEVER change BACKUP_ENCRYPTION_KEY** - Will lose access to all previous backups
- **_NoOpCache fallback** - When Upstash Redis unavailable, falls back to no-op cache (no external Redis needed)
- **API keys at runtime** - Services must check keys at runtime, not import time

### Security & Authentication
- **JWT endpoints exempted from CSRF** - Configured in `app/core/csrf.py`
- **RS256 JWT with HS256 fallback** - Keys in backend/keys/ (gitignored)
- **48 endpoints secured** - 6 public, 42 protected (verified Aug 25, 2025)
- **CSRF protection** - Double-submit cookie pattern with strategic exemptions
- **CSP blocks Web Workers** - `security_headers.py` sets `worker-src: 'none'`. Must update to `worker-src: 'self' blob:` for focus timer Worker to function in production.

### Frontend & Deployment
- **Frontend on Vercel** - SPA routing via CF Worker proxy (no vercel.json needed when accessed through aistudyarchitect.com)
- **Cloudflare Worker routing** - MUST NOT strip /api prefix, backend expects full paths
- **API docs blocked** - Worker returns 404 for /api/docs, /api/openapi.json, /api/redoc
- **Browser caching** - Chrome aggressively caches ES modules, use cache-busting strategies
- **MUI still installed** - Used by chat, content, and auth form components. Phase 3 removal pending. MUI + Emotion bundled as `mui-vendor` chunk in vite.config.ts rollupOptions.

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Empty/blank AI responses | Use @property for runtime API key loading + streaming wrapper |
| PostgreSQL version mismatch | Python backup using psycopg2 (automatic fallback) |
| CSRF 403 on API calls | JWT endpoints exempted in `app/core/csrf.py` |
| Database free tier expiring | Upgrade to Basic-256mb plan ($6/month) |
| Redis connection fails | _NoOpCache automatically takes over (Upstash REST) |
| Frontend 404 on direct route | CF Worker proxies all non-API to Vercel (SPA routing). Direct Vercel access (`*.vercel.app`) may need vercel.json if ever exposed. |
| File upload fails on Windows | Uncomment `python-magic-bin` in requirements.txt |
| Streaming responses not working | Check SSE implementation in AI service manager |
| Tailwind classes not applying | Ensure `@import "tailwindcss"` in index.css, `@tailwindcss/vite` in vite.config.ts |
| shadcn component not found | Run `npx shadcn@latest add <component>`, check components.json aliases |
| Focus timer blocked in production | Update `worker-src` in security_headers.py from `'none'` to `'self' blob:` |

## Key Technologies & Dependencies

### Backend (Python 3.11+)
- **Framework**: FastAPI 0.109.0
- **Database**: SQLAlchemy 2.0.35 + PostgreSQL (pg8000/psycopg2-binary)
- **Authentication**: python-jose[cryptography], passlib[bcrypt]
- **AI/ML**: anthropic 0.39.0, openai 1.35.0 (LangChain removed)
- **Caching**: Upstash Redis (REST API via httpx, with _NoOpCache fallback)
- **File Processing**: PyPDF2, python-docx, python-pptx, Pillow, pytesseract
- **Cloud Storage**: boto3 (AWS S3 for backups)
- **Testing**: pytest 7.4.4, pytest-asyncio, pytest-cov
- **Code Quality**: ruff 0.1.11, mypy 1.8.0

### Frontend (Node.js 20+)
- **Framework**: React 18 with TypeScript 5.3.3 (strict mode)
- **Build Tool**: Vite 6.4.1 with @tailwindcss/vite plugin
- **Styling**: Tailwind CSS v4.2.1 (CSS-first @theme config, no tailwind.config.js)
- **UI Primitives**: shadcn/ui (Radix-based: dialog, dropdown-menu, tabs, slot) + CVA (class-variance-authority)
- **UI Legacy**: Material-UI 5.15.3 + Emotion (chat, content, auth forms — Phase 3 removal)
- **Icons**: Lucide React (new components), MUI Icons (legacy components)
- **Charts**: visx (heatmap, scale, responsive, shape, axis, group, tooltip, xychart)
- **State Management**: @tanstack/react-query 5.17.9, Zustand 5.0.11
- **HTTP Client**: Axios 1.6.5
- **Forms**: react-hook-form 7.48.2 + Zod 4.3.6 + @hookform/resolvers 5.2.2
- **Routing**: react-router-dom 6.21.1
- **Markdown**: react-markdown 10.1.0, rehype-highlight, remark-gfm
- **Fonts**: @fontsource (Space Grotesk, JetBrains Mono, Inter) — self-hosted, no CDN
- **Notifications**: sonner 2.0.7
- **File Upload**: react-dropzone 14.2.3
- **Date**: date-fns 3.2.0
- **Error Tracking**: @sentry/react + @sentry/vite-plugin
- **Testing**: Vitest 1.2.0, Playwright 1.55.0, @testing-library/react 14.1.2, happy-dom, jest-axe
- **Code Quality**: ESLint 8 (React + TypeScript), prettier-plugin-tailwindcss, husky + lint-staged

### CI/CD
- **GitHub Actions**: Node 20, Python 3.11
- **Staging** (staging.yml): test on push to develop/staging, PR to main. PostgreSQL 17 service container.
- **Deploy** (deploy.yml): security scan (semgrep via pipx), migrations, CF Worker deploy
- **Claude Review** (claude-code-review.yml): AI-powered PR review with Claude Sonnet 4.6
- **Backup** (backup.yml): automated database backups

## Documentation Index

**Primary Documentation:**
- [README.md](README.md) - Project overview and CS50 submission
- [CLAUDE.md](CLAUDE.md) - This file - AI assistant guidance
- [DEVELOPMENT.md](DEVELOPMENT.md) - Local setup and development workflow
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide

**Strategic Direction:**
- [docs/direction/NEW_DIRECTION_2025.md](docs/direction/NEW_DIRECTION_2025.md) — Canonical strategic document

**Technical:**
- [docs/technical/ARCHITECTURE.md](docs/technical/ARCHITECTURE.md) — System architecture
- [docs/technical/IMPLEMENTATION_STATUS.md](docs/technical/IMPLEMENTATION_STATUS.md) — Current status
- [docs/technical/API_REFERENCE.md](docs/technical/API_REFERENCE.md) — API documentation

**Planning:**
- [docs/planning/DAILY_DEV_PLAN.md](docs/planning/DAILY_DEV_PLAN.md) — Daily dev sessions
- [docs/plans/2026-03-14-001-feat-full-product-build-phases-neg1-0-1-plan.md](docs/plans/2026-03-14-001-feat-full-product-build-phases-neg1-0-1-plan.md) — Full build plan (deepened, reviewed)

**Design:**
- [design/README.md](design/README.md) — Stitch design pipeline
- [design/DESIGN.md](design/DESIGN.md) — Canonical design system (tokens, typography, components, glow recipes)
- [design/PRD.md](design/PRD.md) — Analytics Pro PRD (4 screens)
- `design/stitch/v1-analytics-pro/` — 4 mobile screens (original)
- `design/stitch/v2-mixed/` — 4 desktop screens (mixed aesthetic)
- `design/stitch/v3-evolved/` — 4 desktop screens (evolved IA: mastery metrics replace gamification)

**Brainstorms:**
- [docs/brainstorms/2026-03-13-mvp-frontend-brainstorm.md](docs/brainstorms/2026-03-13-mvp-frontend-brainstorm.md) — Stack decisions, tool audit, research findings

**Solutions:**
- [docs/solutions/](docs/solutions/) — Documented patterns, bug fixes, and past mistakes

**Vision:**
- [docs/vision/](docs/vision/) — Product DNA (Karpathy, PG, genesis, philosophy)

**Full docs index:** [docs/README.md](docs/README.md)

## Best Practices for AI Assistants

### Before Starting Work
1. Check `docs/solutions/` for documented patterns and past mistakes before implementing anything similar
1. Read [docs/README.md](docs/README.md) for documentation overview
2. Review recent commits to understand latest changes
3. Check [docs/technical/IMPLEMENTATION_STATUS.md](docs/technical/IMPLEMENTATION_STATUS.md) for current state
4. Understand the mastery-based learning focus (see [docs/direction/](docs/direction/))

### During Development
1. Follow the NO EMOJIS rule strictly
2. Use TDD approach when possible
3. Write clear, descriptive commit messages
4. Update IMPLEMENTATION_STATUS.md when completing features
5. Test on Windows and Linux if possible
6. New UI components: use Tailwind + shadcn/ui (not MUI)
7. Use design tokens from `@theme` in `src/index.css` — never hardcode hex colors
8. Use `cn()` from `@/lib/utils` for conditional class merging

### Code Style
1. Backend: Follow PEP 8, use type hints, document with docstrings
2. Frontend: Follow React/TypeScript best practices, use functional components
3. Use ruff for Python linting, ESLint for TypeScript
4. Tailwind class order: sorted by prettier-plugin-tailwindcss
5. Run tests before committing

### Git Workflow
1. Create feature branches from main
2. Use descriptive branch names (e.g., `feat/knowledge-graph-extraction`)
3. Write clear commit messages following conventional commits
4. Test thoroughly before creating PRs
5. Update documentation with code changes

## Quick Reference: File Locations

**Configuration:**
- Backend config: `backend/app/core/config.py`
- Environment template: `.env.example`
- Database migrations: `backend/alembic/versions/`
- Frontend Vite config: `frontend/vite.config.ts`
- Frontend TypeScript config: `frontend/tsconfig.json`
- shadcn/ui config: `frontend/components.json`
- Design tokens: `frontend/src/index.css` (@theme block)
- Design system: `design/DESIGN.md`

**API Endpoints:**
- Main router: `backend/app/api/v1/api.py`
- Auth: `backend/app/api/v1/auth.py`
- Chat: `backend/app/api/v1/chat.py`
- Tutor: `backend/app/api/v1/tutor.py`
- Admin: `backend/app/api/v1/admin.py`
- Subjects: `backend/app/api/v1/subjects.py`
- Sessions: `backend/app/api/v1/study_sessions.py`
- Dashboard: `backend/app/api/v1/dashboard.py`

**AI Services:**
- Service manager: `backend/app/services/ai_service_manager.py`
- Claude integration: `backend/app/services/claude_service.py`
- OpenAI fallback: `backend/app/services/openai_fallback.py`

**Frontend — Pages:**
- Dashboard: `frontend/src/pages/DashboardPage.tsx`
- Study/Chat: `frontend/src/pages/StudyPage.tsx`
- Focus Timer: `frontend/src/pages/FocusPage.tsx`
- Content: `frontend/src/pages/ContentPage.tsx`

**Frontend — Layout:**
- App shell: `frontend/src/app/layout/AppShell.tsx`
- Navigation: `frontend/src/app/layout/TopNav.tsx`

**Frontend — Components:**
- Auth: `frontend/src/components/auth/` (MUI — legacy)
- Chat: `frontend/src/components/chat/` (MUI — legacy)
- Content: `frontend/src/components/content/` (MUI — legacy)
- Dashboard: `frontend/src/components/dashboard/` (Tailwind + visx)
- UI primitives: `frontend/src/components/ui/` (shadcn/ui)

**Frontend — Infrastructure:**
- Utility: `frontend/src/lib/utils.ts` (cn helper)
- Timer hook: `frontend/src/hooks/useTimer.ts`
- Timer worker: `frontend/src/workers/timer.worker.ts`
- Sentry config: `frontend/src/config/sentry.ts`
- Test setup: `frontend/src/test/setup.ts`

## Current Development Focus

**Phase 1 complete**: Tailwind v4 foundation, dashboard UI (HeroMetrics, SubjectList, ContributionHeatmap, StartFocusCTA), backend APIs (subjects, sessions, dashboard summary), focus timer with Web Worker.

**Implementation Status:**
- Lead Tutor Agent with Socratic questioning: COMPLETE
- Multi-provider AI integration: COMPLETE
- File upload and processing: COMPLETE
- Chat interface with streaming: COMPLETE
- Analytics dashboard UI (Tailwind + shadcn): COMPLETE (Phase 1)
- Subject CRUD backend: COMPLETE
- Session lifecycle backend (start/pause/resume/stop): COMPLETE
- Dashboard summary API (3-query pattern): COMPLETE
- Focus timer with Web Worker: COMPLETE
- Stitch v3 evolved designs (mastery metrics, no gamification): COMPLETE
- MUI removal from legacy components: Phase 3 (pending)
- Subject Detail page: Phase 2
- Weekly Analytics page: Phase 2/5
- Knowledge Graph extraction: Phase 2
- Practice generation: Phase 2
- Mastery gates: Phase 2
- Spaced repetition: Phase 2

See [docs/technical/IMPLEMENTATION_STATUS.md](docs/technical/IMPLEMENTATION_STATUS.md) for detailed status.

---

**Last Updated**: March 2026
**For questions or issues**: Check TROUBLESHOOTING.md or [docs/README.md](docs/README.md).
