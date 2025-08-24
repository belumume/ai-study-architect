# Development Guide

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 17
- Git

### Local Setup

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev  # Runs on port 5173
```

### Environment Variables
Copy `.env.example` to `.env` and configure:

**Required:**
- `ANTHROPIC_API_KEY` - Claude API key (primary AI)
- `OPENAI_API_KEY` - OpenAI API key (fallback)
- `DATABASE_URL` - PostgreSQL connection string

**Optional:**
- Backup system (R2/S3) - See BACKUP_SETUP.md
- Redis (falls back to in-memory if not configured)

## Testing

### Backend Tests
```bash
cd backend
pytest tests/                                   # All tests
pytest tests/test_auth.py                      # Specific file
pytest -v -s                                    # Verbose with prints
coverage run -m pytest && coverage report      # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test                  # Run tests with Vitest
npm run test:ui          # Run tests with UI
npm run test:coverage    # Generate coverage report
npm run typecheck        # Check TypeScript types
npm run lint             # Lint code with ESLint
```

### Quick Integration Tests
```bash
# Test Socratic mode
venv\Scripts\python.exe backend/tests/scripts/quick_socratic_test.py

# Test Claude API directly
venv\Scripts\python.exe backend/tests/scripts/test_claude_api.py
```

## Code Quality

### Backend
```bash
ruff check app/           # Lint code
ruff check app/ --fix    # Auto-fix issues
```

### Frontend
```bash
npm run lint             # ESLint
npm run typecheck       # TypeScript
```

## Git Workflow

### Committing Changes
```bash
git add .
git status
git commit -m "feat: Add feature description"
git push
```

### Commit Message Format
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting, no code change
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance

## Deployment

### Automatic Deployment
- **Frontend**: Push to main → Vercel auto-deploys
- **Backend**: Push to main → Render auto-deploys

### Manual Database Migration
```bash
# Only if schema changes
alembic upgrade head
```

## Common Tasks

### Add a New Agent
1. Create agent file in `backend/app/agents/`
2. Register in `backend/app/api/v1/endpoints/agents.py`
3. Add frontend interface in `frontend/src/services/api.ts`

### Update Dependencies
```bash
# Backend
pip freeze > requirements.txt

# Frontend
npm update
```

### Create Database Backup
```bash
# Trigger manual backup
curl -X POST -H "X-Backup-Token: YOUR_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/trigger
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Architecture Decisions

- **FastAPI** for backend - async, fast, modern Python
- **React + TypeScript** for frontend - type safety, component reusability
- **PostgreSQL** for database - robust, scalable, full-text search
- **Claude API** primary, OpenAI fallback - best educational performance
- **Render + Vercel** hosting - simple deployment, good free tiers

## Security Considerations

- JWT authentication with RS256
- CSRF protection on state-changing operations
- Rate limiting on all endpoints
- Input validation with Pydantic
- Encrypted backups with Fernet

## Performance Optimizations

- Redis caching for session state (falls back to in-memory)
- Database connection pooling
- Frontend code splitting
- Lazy loading of components
- SSE for streaming responses

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Claude API](https://docs.anthropic.com/)
- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)