# Deployment Guide - AI Study Architect

## Current Production Deployment

- **Backend API**: https://ai-study-architect.onrender.com
- **Frontend**: [To be deployed on Vercel]
- **Status**: Backend live and operational

## Quick Deploy to Render

### Prerequisites
1. GitHub account
2. Render account (free tier works)
3. API keys for Claude (primary) and OpenAI (fallback)

### Backend Deployment

1. **Connect GitHub Repository**
   - Sign in to [Render](https://render.com)
   - New > Web Service > Connect your GitHub repo
   - Select branch: `main`

2. **Configure Build Settings**
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `./start_render.sh`

3. **Environment Variables** (Dashboard > Environment)
   ```
   ANTHROPIC_API_KEY=sk-ant-xxx  # Primary AI service
   OPENAI_API_KEY=sk-xxx          # Fallback AI service
   SECRET_KEY=[auto-generated]
   BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app
   DATABASE_URL=[auto-provided by Render]
   REDIS_URL=[from Upstash or Redis service]
   ENVIRONMENT=production
   ```

4. **Database Setup**
   - Render provides PostgreSQL automatically
   - After first deploy, manually create database:
   ```bash
   ./build.sh  # Runs migrations
   ```

### Frontend Deployment (Vercel)

1. **Connect Repository**
   - Sign in to [Vercel](https://vercel.com)
   - Import Git Repository > Select your repo

2. **Configure Build**
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Environment Variables**
   ```
   VITE_API_URL=https://ai-study-architect.onrender.com
   ```

## Local Development

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables (.env)
```bash
# Backend
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql://user:pass@localhost:5433/aidb
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
BACKEND_CORS_ORIGINS=http://localhost:5173

# Frontend (.env.local)
VITE_API_URL=http://localhost:8000
```

## Windows-Specific Notes

- PostgreSQL often runs on port 5433 (not 5432)
- Use `venv\Scripts\python.exe` for Python commands
- Password special chars need `quote_plus()` encoding
- Set `WATCHFILES_FORCE_POLLING=True` for hot reload

## Security Checklist

- ✅ Never commit `.env` files
- ✅ Use exact CORS origins (no wildcards in production)
- ✅ RS256 JWT tokens with auto-generated keys
- ✅ CSRF protection on state-changing endpoints
- ✅ Rate limiting configured
- ✅ Input validation on all endpoints

## Troubleshooting

**ModuleNotFoundError**: Check if files are in git: `git ls-files | grep filename`

**CORS 403 Error**: Verify `BACKEND_CORS_ORIGINS` matches exactly (including https://)

**Database Connection**: Render auto-provisions DATABASE_URL, no manual config needed

**Redis Connection**: Use Upstash Redis (free tier) or MockRedis fallback

## Monitoring

- Render Dashboard: Service logs, metrics
- Health Check: `GET /api/v1/health`
- API Docs: `https://ai-study-architect.onrender.com/docs`