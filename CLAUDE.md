# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Study Architect - A 7-agent educational system that builds cognitive strength through Socratic questioning and guided discovery learning. Uses Claude API (primary) and OpenAI (fallback) to help students learn from their own course materials.

**Live Application**: https://ai-study-architect.onrender.com  
**Repository**: https://github.com/belumume/ai-study-architect  
**Core Philosophy**: "Build cognitive strength, not cognitive debt"

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
coverage run -m pytest                         # Run tests with coverage
coverage report                                # Show coverage report

# Database
alembic upgrade head                           # Run migrations (fails in production)
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

### Health Checks
```bash
# Production
curl https://ai-study-architect.onrender.com/api/v1/health
curl https://ai-study-architect.onrender.com/docs

# Local
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/docs
```

### Backup Operations
```bash
# Test backup configuration
curl -X POST -H "X-Backup-Token: YOUR_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/test

# Trigger R2 backup (primary - daily automated)
curl -X POST -H "X-Backup-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "r2"}' \
  https://ai-study-architect.onrender.com/api/v1/backup/trigger

# Trigger S3 backup (secondary - weekly automated)
curl -X POST -H "X-Backup-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "s3"}' \
  https://ai-study-architect.onrender.com/api/v1/backup/trigger

# Check backup status
curl -X GET -H "X-Backup-Token: YOUR_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/status

# Decrypt a backup (local)
python backend/scripts/decrypt_backup.py backup.enc backup.sql
```

## High-Level Architecture

### 7-Agent System
The project implements seven specialized agents that work together to create personalized learning experiences:

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
- `app/api/v1/endpoints/` - RESTful API endpoints organized by feature

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

**Migration Strategy:**
- Alembic for schema versioning
- Pre-existing tables require empty Pre-Deploy command
- Migrations handled in `start_render.sh` with error handling

### AI Integration Architecture

**Multi-Provider Strategy:**
1. **Claude API** (Primary) - Superior educational performance (93.7% HumanEval)
2. **OpenAI API** (Fallback) - Automatic failover for reliability
3. **LangChain** - Orchestration and prompt management

**Key Features:**
- Server-sent events (SSE) for streaming responses
- Token counting and usage tracking
- Context window management
- Prompt template system for consistency

## Deployment Configuration

### Platform Architecture
- **Backend**: Render Starter Plan ($7/month)
- **Frontend**: Vercel (free tier)
- **Database**: PostgreSQL 17 Basic-256mb ($6/month)
- **Caching**: MockRedisClient (in-memory fallback)

### Render Platform Settings
**Critical**: These must match exactly in Render dashboard

```
Root Directory: backend
Build Command: chmod +x build_starter.sh && ./build_starter.sh
Pre-Deploy Command: (MUST BE EMPTY - leave blank)
Start Command: chmod +x start_render.sh && ./start_render.sh
Instance Type: Starter ($7/month)
Database: Basic-256mb ($6/month) - Upgraded from free tier
```

### Required Environment Variables
```bash
# Database (auto-configured by Render)
DATABASE_URL=postgresql://...

# AI Services (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Backup System (Dual-Provider)
BACKUP_TOKEN=<match GitHub secret>
BACKUP_ENCRYPTION_KEY=<NEVER CHANGE - stored in password manager>

# AWS S3 (Secondary - Weekly backups)
AWS_ACCESS_KEY_ID=<your AWS key>
AWS_SECRET_ACCESS_KEY=<your AWS secret>
AWS_BACKUP_BUCKET=ai-study-architect-backup-2025

# Cloudflare R2 (Primary - Daily backups)
R2_ACCOUNT_ID=<your Cloudflare account ID>
R2_ACCESS_KEY=<from R2 API token>
R2_SECRET_KEY=<from R2 API token>
R2_BUCKET=ai-study-architect-backups

# Redis/Caching (REMOVED - using MockRedisClient)
# UPSTASH_REDIS_REST_URL - Not needed
# UPSTASH_REDIS_REST_TOKEN - Not needed

# Auto-generated
SECRET_KEY=<auto-generated>
JWT_SECRET_KEY=<auto-generated>
```

### Backup System
- **Dual-Provider Strategy**: Cloudflare R2 (primary) + AWS S3 (secondary)
- **Schedule**: R2 daily at 2 AM UTC, S3 weekly (Sundays) at 3 AM UTC
- **Encryption**: Fernet (AES-128-CBC + HMAC) - authenticated encryption
- **Storage**: R2 (30-day retention), S3 (14-day retention)
- **Rate Limit**: 1 hour between manual backups
- **Trigger**: GitHub Actions → API endpoint
- **Restore Tested**: ✅ Verified working with decrypt script

## Platform-Specific Considerations

### Windows Development
- PostgreSQL runs on port 5433 (not standard 5432)
- Use `venv\Scripts\python.exe` for virtual environment
- Line endings enforced as LF via `.gitattributes`
- Database passwords with special chars need `quote_plus()` encoding

### Render Platform Constraints
- No root access (use Python packages, not apt-get)
- PostgreSQL client v16, database v17 (handled by Python fallback)
- Starter plan benefits: SSH access, no spin-down, persistent disk
- Database upgraded to Basic-256mb plan (expires Sept 6, 2025)

### Vercel Frontend Hosting
- SPA routing configured via `vercel.json`
- Automatic deployments from GitHub
- Custom domain: aistudyarchitect.com

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| PostgreSQL version mismatch | Python backup using psycopg2 (automatic fallback) |
| Alembic "relation exists" error | Leave Pre-Deploy empty in Render dashboard |
| CSRF 403 on backup endpoint | Backup endpoint exempted in `app/core/csrf.py` |
| Build fails on system packages | Render has no root; use Python alternatives |
| bash\r: command not found | `.gitattributes` enforces Unix line endings |
| Rate limit exceeded on backup | Wait 1 hour between manual triggers |
| Redis connection fails | MockRedisClient automatically takes over |
| Frontend 404 on direct route access | Fixed with `vercel.json` SPA rewrites |
| Database free tier expiring | Upgrade to Basic-256mb plan ($6/month) |

## Security Configuration

### CSRF Protection
Exempted paths configured in `app/core/csrf.py`:
- `/api/v1/backup/` - Token authentication
- `/api/v1/auth/*` - Login/register endpoints
- `/api/v1/content/upload` - File upload with JWT
- `/docs`, `/redoc`, `/openapi.json` - API documentation

### Authentication
- JWT with RS256 algorithm (auto-generated RSA keys)
- Token rotation with refresh tokens
- Rate limiting on all endpoints
- Input validation with Pydantic schemas

## Critical Reminders

- **7 agents always** - Not 5 or 6, the system is designed for 7 specialized agents
- **Pre-Deploy MUST be empty** - Any migration command will fail
- **Port 5433 on Windows** - PostgreSQL uses non-standard port
- **Check RENDER_SETTINGS.md** - Before changing Render dashboard settings
- **Backup token in GitHub secrets** - Must match Render environment variable
- **NEVER change BACKUP_ENCRYPTION_KEY** - Will lose access to all previous backups
- **Encryption is Fernet (AES-128)** - NOT AES-256, includes HMAC authentication
- **Feature flags NOT integrated** - Files exist but unused (for future use)
- **Redis/Upstash REMOVED** - Using MockRedisClient fallback, no external Redis needed
- **Database on Basic-256mb plan** - $6/month, expires Sept 6, 2025
- **Frontend on Vercel** - Not Render, requires `vercel.json` for SPA routing

## Project Philosophy

The project addresses the "AI Learning Paradox" - 86% of students use AI for homework, but MIT research shows they perform 78% worse when AI is removed. Our solution: Build cognitive strength through Socratic questioning rather than providing direct answers.

Key principles:
- Questions over answers
- Understanding over correctness
- Personalized to student's actual materials
- Progressive difficulty based on comprehension
- Privacy-preserving collective intelligence