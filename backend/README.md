# AI Study Architect Backend

**Live API**: https://ai-study-architect.onrender.com  
**API Docs**: https://ai-study-architect.onrender.com/docs

---
Document Level: 4
Created: July 2025
Last Updated: August 2025
Supersedes: None
Status: Active
---

This is the backend API for AI Study Architect, a multi-agent learning system that creates personalized, adaptive study experiences.

## Technology Stack

- **Framework**: FastAPI (sync version for Windows compatibility)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Database Driver**: pg8000 (pure Python, Windows-compatible)
- **Authentication**: JWT tokens (RS256) with passlib[bcrypt]
- **Caching**: MockRedisClient (in-memory fallback, no external Redis needed)
- **AI Integration**: Claude (primary), OpenAI (fallback)
- **AI Framework**: LangChain, LangGraph for agent orchestration
- **Security**: Rate limiting, CSRF protection, security headers
- **Agent Management**: In-memory cache with graceful degradation
- **Task Queue**: Celery with Redis (future enhancement)

## Prerequisites

- Python 3.11+ (tested with 3.13)
- PostgreSQL 14+ (check ports 5432/5433 on Windows)
- Redis (optional - falls back to in-memory cache)
- API Keys: Claude (Anthropic) or OpenAI for cloud deployment

## Setup Instructions

### 1. Create Virtual Environment

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Key environment variables:
- **Database**:
  - `POSTGRES_HOST`: Use `127.0.0.1` (not `localhost`) to avoid IPv6 issues
  - `POSTGRES_PORT`: Check with `netstat -an | findstr :543` (often 5433 on Windows)
  - `POSTGRES_USER`: Use `aiuser` (not `postgres` superuser)
  - `POSTGRES_PASSWORD`: URL-encode special characters with `quote_plus()`
- **Security**:
  - `SECRET_KEY`: Generate with `openssl rand -hex 32`
  - `JWT_SECRET_KEY`: Generate separately for JWT tokens
  - `JWT_ALGORITHM`: Use `RS256` for enhanced security
- **AI Services** (Priority: Claude → OpenAI):
  - `ANTHROPIC_API_KEY`: For Claude (best for education)
  - `OPENAI_API_KEY`: For OpenAI fallback
- **Caching** (Optional - falls back to MockRedisClient):
  - `REDIS_URL`: Default `redis://localhost:6379/0` (not required)

### 4. Database Setup

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed PostgreSQL setup instructions.

Quick setup:
```sql
-- Connect as postgres superuser
psql -U postgres -h 127.0.0.1 -p 5432

-- Create application user and database
CREATE USER aiuser WITH PASSWORD 'your_password';
CREATE DATABASE ai_study_architect OWNER aiuser;
GRANT ALL PRIVILEGES ON DATABASE ai_study_architect TO aiuser;
\q
```

**Note**: The application creates tables automatically on first run using SQLAlchemy.

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Windows with specific Python
.\venv\Scripts\python -m uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   │   ├── v1/        # API v1 routes
│   │   └── dependencies.py
│   ├── core/          # Core configuration
│   │   ├── config.py  # Settings management
│   │   ├── database.py # Database connection
│   │   └── security.py # Security utilities
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   │   └── ai/        # AI/ML services
│   └── main.py        # FastAPI application
├── alembic/           # Database migrations
├── tests/             # Test suite
├── requirements.txt   # Python dependencies
└── .env.example       # Environment template
```

## API Endpoints

### Core
- `GET /health` - Health check endpoint
- `GET /api/v1/csrf/token` - Get CSRF token for state-changing operations

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login (returns access & refresh tokens)
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/logout` - Logout (invalidate refresh token)

### Content Management
- `POST /api/v1/content/upload` - Upload study materials (PDF, notes, etc.)
- `GET /api/v1/content` - List user's content
- `GET /api/v1/content/{id}` - Get content details
- `DELETE /api/v1/content/{id}` - Delete content

### AI Tutor
- `POST /api/v1/tutor/chat` - Chat with Lead Tutor agent
- `GET /api/v1/tutor/study-plan` - Get personalized study plan
- `POST /api/v1/tutor/adapt-difficulty` - Adjust difficulty based on performance

### Agents (7-Agent System - Live)
- `POST /api/v1/agents/content-understanding` - Process educational materials ✅ Live
- `POST /api/v1/agents/knowledge-synthesis` - Create concept connections ✅ Live
- `POST /api/v1/agents/practice-generation` - Generate custom exercises ✅ Live
- `POST /api/v1/agents/progress-tracking` - Monitor learning patterns ✅ Live
- `POST /api/v1/agents/assessment` - Evaluate comprehension ✅ Live
- `POST /api/v1/agents/collaboration` - Enable collective intelligence ✅ Live

### Admin (Protected)
- `POST /api/v1/admin/rotate-keys` - Rotate JWT signing keys
- `GET /api/v1/admin/database/pool` - Database pool statistics
- `GET /api/v1/admin/agents/status` - Agent manager statistics
- `GET /api/v1/admin/cache/status` - Redis cache metrics

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py -v
```

### Code Quality

```bash
# Linting
ruff check .
ruff format .

# Type checking
mypy app/

# All checks before commit
ruff check . && ruff format . && mypy app/ && pytest
```

### Database Migrations

```bash
# Windows: Use venv Python
./venv/Scripts/python.exe -m alembic revision --autogenerate -m "Description"

# Linux/Mac
alembic revision --autogenerate -m "Description"

# Apply migrations
./venv/Scripts/python.exe -m alembic upgrade head

# Check current version
./venv/Scripts/python.exe -m alembic current

# Rollback one migration
./venv/Scripts/python.exe -m alembic downgrade -1

# For existing databases, stamp with initial migration
./venv/Scripts/python.exe -m alembic stamp head
```

**Note**: On Windows, always use the venv Python to run Alembic commands to ensure proper module access.

## Windows-Specific Notes

1. **PostgreSQL Port Conflicts**: 
   - WSL PostgreSQL often uses 5432
   - Windows PostgreSQL then uses 5433
   - Always check: `netstat -an | findstr :543`

2. **Password Special Characters**: 
   - Characters like `$`, `&`, `@` need URL encoding
   - Use `urllib.parse.quote_plus()` for connection strings

3. **Environment Variable Issues**:
   - Parent directory `.env` files can override settings
   - WSL environment variables don't carry to Windows
   - Use absolute paths in pydantic settings

4. **Sync vs Async**: 
   - pg8000 doesn't support async operations
   - Using sync SQLAlchemy with proper connection pooling

5. **Module Caching Issues**:
   - Uvicorn may cache modules on Windows/WSL
   - If endpoints don't appear, restart PC or use `--reload`

## Security Considerations

- **Authentication**: 
  - Passwords hashed with bcrypt (cost factor 12)
  - JWT tokens using RS256 algorithm (not HS256)
  - Access tokens expire in 30 minutes
  - Refresh tokens expire in 7 days
  
- **Security Features**:
  - Rate limiting on all endpoints (5/minute for auth)
  - CSRF protection for state-changing operations
  - Comprehensive security headers (CSP, HSTS, etc.)
  - CORS restricted to specific origins
  
- **Data Protection**:
  - Input validation and sanitization
  - SQL injection protection via parameterized queries
  - XSS prevention in all user inputs
  - File upload validation (content + extension)

## Troubleshooting

### PostgreSQL Connection Issues

1. Check which port PostgreSQL is running on:
   ```powershell
   netstat -an | findstr :543
   ```

2. Verify service is running:
   ```powershell
   Get-Service -Name "*postgresql*"
   ```

3. Test connection:
   ```python
   # Test with psql or pg8000 directly
   python -c "import pg8000; print('pg8000 installed')"
   ```

### Common Issues

- **"password authentication failed"**: 
  - Check port (5432 vs 5433)
  - Use `127.0.0.1` instead of `localhost`
  - Verify no parent `.env` files are overriding settings
  
- **"CREATE TYPE permission denied"**: 
  - pg8000 limitation - use CHECK constraints instead of ENUMs
  
- **Module import errors**: 
  - Ensure virtual environment is activated
  - On Windows: `.\venv\Scripts\activate`
  
- **CORS errors**: 
  - Check `BACKEND_CORS_ORIGINS` in `.env`
  - Must include full URL: `http://localhost:3000`
  
- **Endpoints returning 404**:
  - Uvicorn module caching issue on Windows
  - Try: Restart server or PC
  - Force imports in `api.py`

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Run all quality checks
4. Submit pull request

## License

This project is part of CS50's final project submission.