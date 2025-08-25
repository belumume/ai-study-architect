# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Study Architect - A 7-agent educational system that builds cognitive strength through Socratic questioning and guided discovery learning. Uses Claude API (primary) and OpenAI (fallback) to help students learn from their own course materials.

**Live Application**: https://ai-study-architect.onrender.com  
**Core Philosophy**: "Build cognitive strength, not cognitive debt"

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
npm run build                                 # Build for production
npm run preview                               # Preview production build
```

### E2E Testing
```bash
cd frontend
npx playwright test                           # Run all E2E tests
npx playwright test --ui                      # Run with UI mode
npx playwright test streaming-scroll          # Run specific test
```

## High-Level Architecture

### 7-Agent System
The project implements seven specialized agents that work together:

1. **Lead Tutor** (`/api/v1/agents/chat`) - Orchestrates Socratic questioning
2. **Content Understanding** - Processes course materials (PDFs, notes, lectures)
3. **Knowledge Synthesis** (`/api/v1/agents/explain`) - Creates personalized explanations
4. **Practice Generation** (`/api/v1/agents/study-plan`) - Generates adaptive problems
5. **Progress Tracking** (`/api/v1/agents/status`) - Monitors learning patterns
6. **Assessment** (`/api/v1/agents/check-understanding`) - Evaluates comprehension
7. **Collaboration** (`/api/v1/agents/clear-memory`) - Enables collective intelligence

### Backend Architecture (FastAPI)

**Core Components:**
- `app/main.py` - FastAPI application with comprehensive middleware stack
- `app/agents/` - Agent implementations with Redis caching for state management
- `app/services/claude_service.py` - Claude API integration with streaming support
- `app/core/security.py` - JWT authentication with RS256 algorithm
- `app/core/csrf.py` - CSRF protection with strategic exemptions
- `app/models/` - SQLAlchemy models for users, content, sessions, and practice

**Key Design Patterns:**
- Dependency injection for database sessions and authentication
- Service layer pattern for AI integrations
- Repository pattern for data access
- Middleware pipeline for cross-cutting concerns
- Streaming responses for real-time AI interactions

### Frontend Architecture (React + TypeScript)

**Component Structure:**
- `src/components/auth/` - Authentication forms with JWT handling
- `src/components/chat/` - Real-time chat interface with streaming
- `src/components/content/` - File upload with drag-and-drop support
- `src/contexts/AuthContext.tsx` - Global authentication state
- `src/services/api.ts` - Axios client with interceptors for auth/CSRF

**State Management:**
- React Query for server state and caching
- Context API for global auth state
- Local state for component-specific data

### Database Architecture

**PostgreSQL 17** with SQLAlchemy ORM:
- `users` - Authentication and profiles
- `content` - Uploaded study materials with extracted text
- `study_sessions` - Learning sessions and progress tracking
- `practice_problems` - Generated exercises with difficulty levels
- `chat_messages` - Conversation history with context

### AI Integration Architecture

**Multi-Provider Strategy:**
1. **Claude API** (Primary) - Superior educational performance
2. **OpenAI API** (Fallback) - Automatic failover for reliability
3. **LangChain** - Orchestration and prompt management

**Key Features:**
- Server-sent events (SSE) for streaming responses
- Token counting and usage tracking
- Context window management
- Prompt template system for consistency

## Platform-Specific Considerations

### Windows Development
- PostgreSQL runs on port 5433 (not standard 5432)
- Use `venv\Scripts\python.exe` for virtual environment
- Line endings enforced as LF via `.gitattributes`
- Database passwords with special chars need `quote_plus()` encoding

### Render Platform Constraints
- No root access (use Python packages, not apt-get)
- Starter plan benefits: SSH access, no spin-down, persistent disk
- Pre-Deploy command MUST be empty in Render dashboard
- Database upgraded to Basic-256mb plan ($6/month, expires Sept 6, 2025)

### Vercel Frontend Hosting
- SPA routing configured via `vercel.json`
- Automatic deployments from GitHub
- Custom domain: aistudyarchitect.com

## Critical Reminders

- **7 agents always** - Not 5 or 6, the system is designed for 7 specialized agents
- **Pre-Deploy MUST be empty** - Any migration command will fail
- **Port 5433 on Windows** - PostgreSQL uses non-standard port
- **NEVER change BACKUP_ENCRYPTION_KEY** - Will lose access to all previous backups
- **MockRedisClient fallback** - No external Redis needed, uses in-memory fallback
- **API keys at runtime** - Services must check keys at runtime, not import time
- **JWT endpoints exempted from CSRF** - Configured in `app/core/csrf.py`
- **Frontend on Vercel** - Not Render, requires `vercel.json` for SPA routing
- **Cloudflare Worker routing** - MUST NOT strip /api prefix, backend expects full paths
- **API docs blocked** - Worker returns 404 for /api/docs, /api/openapi.json, /api/redoc
- **RS256 JWT with HS256 fallback** - Keys in backend/keys/ (gitignored)
- **48 endpoints secured** - 6 public, 42 protected (verified Aug 25, 2025)

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Empty/blank AI responses | Use @property for runtime API key loading + streaming wrapper |
| PostgreSQL version mismatch | Python backup using psycopg2 (automatic fallback) |
| CSRF 403 on API calls | JWT endpoints exempted in `app/core/csrf.py` |
| Database free tier expiring | Upgrade to Basic-256mb plan ($6/month) |
| Redis connection fails | MockRedisClient automatically takes over |
| Frontend 404 on direct route | Fixed with `vercel.json` SPA rewrites |