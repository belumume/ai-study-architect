# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Study Architect - A mastery-based learning system that proves students actually learned through knowledge graphs, spaced repetition, and measurable retention. Currently focused on CS education (CS50) as beachhead market. Uses Claude API (primary) and OpenAI (fallback) for AI-powered concept extraction and practice generation.

**Live Application**: https://ai-study-architect.onrender.com
**Frontend**: https://aistudyarchitect.com (Vercel hosted, Cloudflare Worker routing)
**Core Philosophy**: "Build cognitive strength, not cognitive debt"

**Current Phase**: Strategic pivot to mastery-based learning (see docs/NEW_DIRECTION_2025.md)
- FROM: "7-agent Socratic chatbot"
- TO: "Mastery-based system with proven retention" (MathAcademy-inspired)

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
  require('@mui/material');
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
**Current Implementation** (as of November 2025):
- Lead Tutor Agent - Provides Socratic questioning and explanations [IMPLEMENTED]
- File upload and content processing [IMPLEMENTED]
- Chat interface with streaming responses [IMPLEMENTED]
- Multi-provider AI integration (Claude primary, OpenAI fallback) [IMPLEMENTED]
- User authentication with JWT (RS256) [IMPLEMENTED]
- PostgreSQL database with session management [IMPLEMENTED]

**Planned Components** (see DAILY_DEV_PLAN.md for timeline):
1. **Knowledge Graph Extractor** - Extract atomic concepts and dependencies from course materials
2. **Practice Problem Generator** - Create auto-graded programming exercises
3. **Mastery Tracker** - Enforce 90%+ gates before concept unlock
4. **Spaced Repetition Scheduler** - SM-2 algorithm for optimal review timing
5. **Retention Analyzer** - Track long-term learning (weeks/months later)

**Legacy Reference** (Original 7-Agent Vision):
The original architecture envisioned 7 specialized agents (Lead Tutor, Content Understanding, Knowledge Synthesis, Practice Generation, Progress Tracking, Assessment, Collaboration). The strategic pivot focuses on measurable mastery-based learning instead.

### Backend Architecture (FastAPI)

**Directory Structure:**
```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── dependencies.py        # Shared dependency injection
│   │   └── v1/
│   │       ├── auth.py           # Authentication endpoints
│   │       ├── chat.py           # Chat/conversation endpoints
│   │       ├── tutor.py          # Tutor agent endpoints
│   │       ├── csrf.py           # CSRF token endpoints
│   │       ├── admin.py          # Admin endpoints
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
│   │   ├── cache.py             # Redis caching (with MockRedis fallback)
│   │   ├── agent_manager.py     # Agent orchestration
│   │   ├── rsa_keys.py          # RSA key management for JWT
│   │   ├── security_headers.py  # Security headers middleware
│   │   ├── exceptions.py        # Custom exception handlers
│   │   └── upstash_cache.py     # Upstash Redis integration
│   ├── models/
│   │   ├── user.py             # User accounts [IMPLEMENTED]
│   │   ├── content.py          # Uploaded materials [IMPLEMENTED]
│   │   ├── study_session.py    # Learning sessions [IMPLEMENTED]
│   │   └── practice.py         # Practice problems [IMPLEMENTED]
│   ├── schemas/
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── content.py          # Content schemas
│   │   ├── study_session.py    # Session schemas
│   │   └── agents.py           # Agent request/response schemas
│   └── services/
│       ├── ai_service_manager.py      # AI service selection (Claude → OpenAI) [IMPLEMENTED]
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
- `app/agents/` - Agent implementations with Redis caching for state management
- `app/services/claude_service.py` - Claude API integration with streaming support
- `app/services/ai_service_manager.py` - Intelligent AI service selection and fallback
- `app/core/security.py` - JWT authentication with RS256 algorithm
- `app/core/csrf.py` - CSRF protection with strategic exemptions
- `app/core/cache.py` - Redis caching with MockRedisClient fallback
- `app/models/` - SQLAlchemy models for users, content, sessions, and practice

**Key Design Patterns:**
- Dependency injection for database sessions and authentication
- Service layer pattern for AI integrations
- Repository pattern for data access
- Middleware pipeline for cross-cutting concerns
- Streaming responses for real-time AI interactions
- Automatic fallback strategy for AI services

### Frontend Architecture (React + TypeScript)

**Directory Structure:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx      # Login component
│   │   │   ├── RegisterForm.tsx   # Registration component
│   │   │   └── ProtectedRoute.tsx # Route protection
│   │   ├── chat/
│   │   │   └── ChatInterface.tsx  # Real-time chat with streaming
│   │   └── content/
│   │       ├── ContentUpload.tsx  # File upload with drag-and-drop
│   │       ├── ContentList.tsx    # Display uploaded content
│   │       └── ContentSelector.tsx # Content selection UI
│   ├── contexts/
│   │   └── AuthContext.tsx        # Global authentication state
│   ├── services/
│   │   ├── api.ts                 # Axios client with interceptors
│   │   ├── auth.service.ts        # Authentication service
│   │   └── tokenStorage.ts        # Token management
│   ├── App.tsx                    # Main application component
│   └── main.tsx                   # Application entry point
├── public/                        # Static assets
├── tests/                         # Frontend tests
│   └── e2e/                      # Playwright E2E tests
└── dist/                          # Build output (gitignored)
```

**Component Structure:**
- `src/components/auth/` - Authentication forms with JWT handling
- `src/components/chat/` - Real-time chat interface with streaming
- `src/components/content/` - File upload with drag-and-drop support
- `src/contexts/AuthContext.tsx` - Global authentication state
- `src/services/api.ts` - Axios client with interceptors for auth/CSRF

**State Management:**
- React Query (@tanstack/react-query) for server state and caching
- Context API for global auth state
- Local state for component-specific data

**UI Framework:**
- Material-UI (@mui/material) for component library
- Emotion for CSS-in-JS styling
- React Hook Form for form management
- React Dropzone for file uploads

### Database Architecture

**PostgreSQL 17** with SQLAlchemy ORM:

**Current Tables:**
- `users` - Authentication and profiles
- `content` - Uploaded study materials with extracted text
- `study_sessions` - Learning sessions and progress tracking
- `practice_problems` - Generated exercises with difficulty levels
- `chat_messages` - Conversation history with context (schema exists, full implementation pending)

**Planned (Week 1-2 of mastery-based development):**
- `concepts` - Atomic learning concepts extracted from materials
- `concept_dependencies` - Prerequisite relationships between concepts
- `user_attempts` - Student problem-solving attempts
- `mastery_status` - Per-concept mastery tracking
- `spaced_repetition_schedule` - Review scheduling (SM-2 algorithm)

### AI Integration Architecture

**Multi-Provider Strategy:**
1. **Claude API** (Primary) - Superior educational performance via Anthropic
2. **OpenAI API** (Fallback) - Automatic failover for reliability
3. **LangChain** - Orchestration and prompt management

**Key Features:**
- Server-sent events (SSE) for streaming responses
- Token counting and usage tracking
- Context window management
- Prompt template system for consistency
- Intelligent service selection with automatic fallback
- Runtime API key validation (not import-time)

**Service Manager Flow:**
```
Request → AI Service Manager
         ↓
    Claude Available?
         ├─ Yes → Claude Service → Stream Response
         └─ No → OpenAI Service → Stream Response
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
- Line endings enforced as LF via `.gitattributes`
- Database passwords with special chars need `quote_plus()` encoding
- May need to uncomment `python-magic-bin` in requirements.txt for file processing

### Render Platform Constraints
- No root access (use Python packages, not apt-get)
- Starter plan benefits: SSH access, no spin-down, persistent disk
- Pre-Deploy command MUST be empty in Render dashboard
- Database upgraded to Basic-256mb plan ($6/month, expires Sept 6, 2025)
- Uses `python-magic` (not python-magic-bin) for file type detection

### Vercel Frontend Hosting
- SPA routing configured via `vercel.json`
- Automatic deployments from GitHub
- Custom domain: aistudyarchitect.com
- Environment variables managed via Vercel dashboard

### Cloudflare Worker Routing
- Routes https://aistudyarchitect.com/api/* to backend (Render)
- MUST NOT strip /api prefix - backend expects full paths
- Returns 404 for /api/docs, /api/openapi.json, /api/redoc (security)
- Handles CORS for cross-origin requests

## Critical Reminders

### Development Workflow
- **Mastery-based focus** - Building for measurable learning outcomes, not agent count
- **Daily dev sessions** - See DAILY_DEV_PLAN.md for 1-2 hour incremental progress
- **Strategic pivot** - Focus on mastery-based features per NEW_DIRECTION_2025.md
- **Documentation hierarchy** - See docs/DOCUMENTATION_HIERARCHY.md for doc structure

### Database & Backend
- **Pre-Deploy MUST be empty** - Any migration command will fail on Render
- **Port 5433 on Windows** - PostgreSQL uses non-standard port
- **NEVER change BACKUP_ENCRYPTION_KEY** - Will lose access to all previous backups
- **MockRedisClient fallback** - No external Redis needed, uses in-memory fallback
- **API keys at runtime** - Services must check keys at runtime, not import time

### Security & Authentication
- **JWT endpoints exempted from CSRF** - Configured in `app/core/csrf.py`
- **RS256 JWT with HS256 fallback** - Keys in backend/keys/ (gitignored)
- **48 endpoints secured** - 6 public, 42 protected (verified Aug 25, 2025)
- **CSRF protection** - Double-submit cookie pattern with strategic exemptions

### Frontend & Deployment
- **Frontend on Vercel** - Not Render, requires `vercel.json` for SPA routing
- **Cloudflare Worker routing** - MUST NOT strip /api prefix, backend expects full paths
- **API docs blocked** - Worker returns 404 for /api/docs, /api/openapi.json, /api/redoc
- **Browser caching** - Chrome aggressively caches ES modules, use cache-busting strategies

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Empty/blank AI responses | Use @property for runtime API key loading + streaming wrapper |
| PostgreSQL version mismatch | Python backup using psycopg2 (automatic fallback) |
| CSRF 403 on API calls | JWT endpoints exempted in `app/core/csrf.py` |
| Database free tier expiring | Upgrade to Basic-256mb plan ($6/month) |
| Redis connection fails | MockRedisClient automatically takes over |
| Frontend 404 on direct route | Fixed with `vercel.json` SPA rewrites |
| File upload fails on Windows | Uncomment `python-magic-bin` in requirements.txt |
| Streaming responses not working | Check SSE implementation in AI service manager |

## Key Technologies & Dependencies

### Backend (Python 3.11+)
- **Framework**: FastAPI 0.109.0
- **Database**: SQLAlchemy 2.0.35 + PostgreSQL (pg8000/psycopg2-binary)
- **Authentication**: python-jose[cryptography], passlib[bcrypt]
- **AI/ML**: langchain 0.3.27, anthropic 0.39.0, openai 1.35.0
- **Caching**: redis 5.0.1 (with MockRedis fallback)
- **File Processing**: PyPDF2, python-docx, python-pptx, Pillow, pytesseract
- **Cloud Storage**: boto3 (AWS S3 for backups)
- **Testing**: pytest 7.4.4, pytest-asyncio, pytest-cov
- **Code Quality**: ruff 0.1.11, mypy 1.8.0

### Frontend (Node.js 18+)
- **Framework**: React 18 with TypeScript 5.3.3
- **Build Tool**: Vite 5.0.11
- **UI Library**: Material-UI 5.15.3
- **State Management**: @tanstack/react-query 5.17.9
- **HTTP Client**: Axios 1.6.5
- **Forms**: react-hook-form 7.48.2
- **Routing**: react-router-dom 6.21.1
- **File Upload**: react-dropzone 14.2.3
- **Testing**: Vitest 1.2.0, Playwright 1.55.0, @testing-library/react 14.1.2

## Documentation Index

**Primary Documentation:**
- [README.md](README.md) - Project overview and CS50 submission
- [CLAUDE.md](CLAUDE.md) - This file - AI assistant guidance
- [DEVELOPMENT.md](DEVELOPMENT.md) - Local setup and development workflow
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide

**Strategic Direction:**
- [docs/NEW_DIRECTION_2025.md](docs/NEW_DIRECTION_2025.md) - Strategic pivot to mastery-based learning
- [DAILY_DEV_PLAN.md](DAILY_DEV_PLAN.md) - 1-2 hour daily development sessions
- [STRATEGIC_PIVOT_SUMMARY.md](STRATEGIC_PIVOT_SUMMARY.md) - Pivot summary

**Architecture & Implementation:**
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture details
- [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) - Current implementation status
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - API documentation

**Security & Operations:**
- [SECURITY.md](SECURITY.md) - Security implementation
- [SECURITY_AUDIT_2025.md](SECURITY_AUDIT_2025.md) - Security audit procedures
- [BACKUP_SECURITY.md](BACKUP_SECURITY.md) - Backup system architecture
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

**Project History & Vision:**
- [docs/PROJECT_GENESIS.md](docs/PROJECT_GENESIS.md) - How the project started
- [docs/PROBLEM_STATEMENT.md](docs/PROBLEM_STATEMENT.md) - The AI learning paradox
- [docs/COLLECTIVE_INTELLIGENCE_VISION.md](docs/COLLECTIVE_INTELLIGENCE_VISION.md) - Future collective learning vision

## Best Practices for AI Assistants

### Before Starting Work
1. Read relevant documentation (check DOCUMENTATION_INDEX.md)
2. Review recent commits to understand latest changes
3. Check IMPLEMENTATION_STATUS.md for current state
4. Understand the mastery-based learning focus

### During Development
1. Follow the NO EMOJIS rule strictly
2. Use TDD approach when possible
3. Write clear, descriptive commit messages
4. Update IMPLEMENTATION_STATUS.md when completing features
5. Test on Windows and Linux if possible

### Code Style
1. Backend: Follow PEP 8, use type hints, document with docstrings
2. Frontend: Follow React/TypeScript best practices, use functional components
3. Use ruff for Python linting, ESLint for TypeScript
4. Run tests before committing

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
- Frontend config: `frontend/vite.config.ts`

**API Endpoints:**
- Auth: `backend/app/api/v1/auth.py`
- Chat: `backend/app/api/v1/chat.py`
- Tutor: `backend/app/api/v1/tutor.py`
- Admin: `backend/app/api/v1/admin.py`

**AI Services:**
- Service manager: `backend/app/services/ai_service_manager.py`
- Claude integration: `backend/app/services/claude_service.py`
- OpenAI fallback: `backend/app/services/openai_fallback.py`

**Frontend Components:**
- Auth: `frontend/src/components/auth/`
- Chat: `frontend/src/components/chat/`
- Content: `frontend/src/components/content/`

## Current Development Focus (November 2025)

As outlined in DAILY_DEV_PLAN.md, the current focus is on implementing the mastery-based learning system:

**Week 1-2 Goals:**
1. Knowledge Graph database schema (concepts, concept_dependencies)
2. Concept extraction service using Claude API
3. Knowledge Graph API endpoints
4. Testing with real CS50 materials

**Implementation Status:**
- Lead Tutor Agent with Socratic questioning: ✅ COMPLETE
- Multi-provider AI integration: ✅ COMPLETE
- File upload and processing: ✅ COMPLETE
- Chat interface with streaming: ✅ COMPLETE
- Knowledge Graph extraction: ❌ PLANNED (Week 1-2)
- Practice generation: ❌ PLANNED (Week 3-4)
- Mastery gates: ❌ PLANNED (Week 5-6)
- Spaced repetition: ❌ PLANNED (Week 6-7)

See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for detailed status tracking.

---

**Last Updated**: November 2025
**For questions or issues**: Check TROUBLESHOOTING.md or review the documentation index above.
