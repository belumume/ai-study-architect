# AI Study Architect - Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (running on port 5432 or 5433)
- Redis 6+ (required for caching and session management)
- AI Service (cloud-only for reliability):
  - Claude API key (Anthropic) - Primary, best for education
  - OpenAI API key - Automatic fallback

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/yourusername/ai-study-architect.git
cd ai-study-architect
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac/WSL
python3 -m venv venv
source venv/bin/activate
```

> **Windows Note**: If you get "scripts cannot be executed" error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

#### Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

#### Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Key settings to update:
# - POSTGRES_PASSWORD
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - JWT_SECRET_KEY (generate separately)
# - ANTHROPIC_API_KEY (get from console.anthropic.com)
# - OPENAI_API_KEY (automatic fallback, from platform.openai.com)
```

#### Database Setup

```bash
# Check PostgreSQL port (Windows often uses 5433)
netstat -an | findstr "5432 5433"

# Connect as postgres superuser
psql -U postgres -h 127.0.0.1 -p 5432

# Create database and user
CREATE USER aiuser WITH PASSWORD 'your_secure_password';
CREATE DATABASE ai_study_architect OWNER aiuser;
GRANT ALL PRIVILEGES ON DATABASE ai_study_architect TO aiuser;
\q

# Run migrations
alembic upgrade head
```

> **Important**: Use `127.0.0.1` instead of `localhost` to avoid IPv6 issues on Windows

#### Generate RSA Keys (First Time Only)

```bash
python scripts/generate_rsa_keys.py
```

#### Start Backend Server

```bash
# From backend directory with venv activated
uvicorn app.main:app --reload

# Or if uvicorn is not in PATH:
python -m uvicorn app.main:app --reload

# Alternative port if 8000 is in use:
uvicorn app.main:app --reload --port 8001
```

Backend API available at:
- http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 3. Frontend Setup

Open a new terminal window:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Or open browser automatically
npm run dev -- --open
```

Frontend available at http://localhost:5173 (or 5174 if port is in use)

### 4. Optional Services

#### Redis (Caching)

```bash
# Windows: Install Redis via WSL or use Memurai
# Check if running
redis-cli ping

# Default port is 6379, project may use 6380
redis-cli -p 6380 ping
```

#### AI Services Configuration

The app uses cloud-only AI architecture with intelligent service selection (Claude → OpenAI).

**Claude (Primary - Recommended for Best Educational Experience)**
```bash
# Get API key from https://console.anthropic.com/
# Add to .env:
ANTHROPIC_API_KEY=sk-ant-...
```

**OpenAI (Automatic Fallback)**
```bash
# Get API key from https://platform.openai.com/api-keys
# Add to .env:
OPENAI_API_KEY=sk-...
```

The app automatically uses Claude for primary AI operations and falls back to OpenAI if needed. Configure both services for maximum reliability.

## Platform-Specific Notes

### Windows

1. **PowerShell vs Command Prompt**: Use PowerShell for better compatibility
2. **Path Separators**: The project handles both `/` and `\` automatically
3. **Port Conflicts**: WSL PostgreSQL often uses 5432, Windows uses 5433
4. **File Watchers**: Set `WATCHFILES_FORCE_POLLING=True` for hot reload issues

### macOS

1. **PostgreSQL**: Install via Homebrew: `brew install postgresql`
2. **Port Access**: May need to allow connections in System Preferences
3. **Python Version**: Use pyenv for version management

### Linux/WSL

1. **Permissions**: May need sudo for port binding below 1024
2. **PostgreSQL**: Usually available via system package manager
3. **systemd**: Can set up services for production deployment

## Verification Steps

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy"}
   ```

2. **Database Connection**:
   ```python
   # Quick test
   python -c "from app.core.database import test_connection; print(test_connection())"
   ```

3. **Frontend API Connection**:
   - Open browser DevTools Network tab
   - Navigate to http://localhost:5173
   - Should see successful API calls to `/api/v1/csrf/token`

4. **Authentication Flow**:
   - Click "Sign up" on login page
   - Create test account
   - Verify login/logout works
   - Check user menu in top-right

## Common Issues & Solutions

### Backend Won't Start

- **Port in use**: Kill process or use different port
- **Module not found**: Ensure venv is activated
- **Database error**: Check PostgreSQL is running and credentials are correct

### Frontend Connection Issues

- **CORS errors**: Backend must be running first
- **Wrong API URL**: Check vite.config.ts proxy settings
- **Port changed**: Vite shows actual port in terminal

### Database Connection Failed

```bash
# Debug checklist
1. Check PostgreSQL service is running
2. Verify port: netstat -an | findstr :543
3. Use 127.0.0.1 instead of localhost
4. Check password encoding (special characters)
5. Verify pg_hba.conf allows connections
```

### Redis Connection Issues

- **Not required**: App works without Redis (graceful degradation)
- **Wrong port**: Check REDIS_PORT in .env
- **WSL issue**: Ensure Redis binds to 0.0.0.0, not just localhost

## Development Workflow

1. **Always activate venv** before working on backend
2. **Run tests** before commits: `pytest`
3. **Check code quality**: 
   ```bash
   # Backend
   ruff check backend/
   mypy backend/
   
   # Frontend
   npm run typecheck
   npm run lint
   ```
4. **Use proper branch strategy**: feature/*, bugfix/*, etc.

## Security Reminders

- Never commit `.env` files
- RSA keys are auto-generated, don't share
- Use strong passwords even in development
- Enable HTTPS for production deployment

## Next Steps

1. ✅ Create your first user account
2. ✅ Upload study materials (PDF, DOCX, etc.)
3. 🚧 Try the AI tutor chat (when implemented)
4. 📋 Check the todo list in the app
5. 🎯 Start implementing features!

## Getting Help

- API Documentation: http://localhost:8000/docs
- Project Structure: See `docs/ARCHITECTURE.md`
- Security Guidelines: See `backend/SECURITY_STATUS.md`
- Database Details: See `backend/DATABASE_SETUP.md`

---

*For detailed Windows-specific issues, PostgreSQL setup, or architectural decisions, refer to the specialized documentation in the `docs/` folder.*