# Documentation Index

## 📚 Core Documentation

### Project Overview
- **[README.md](README.md)** - CS50 final project submission, overview, and features
- **[CLAUDE.md](CLAUDE.md)** - Claude Code development guidance and commands

### Development & Operations
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Local setup, testing, and development workflow
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment, monitoring, and operations
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### Security & Backup
- **[SECURITY.md](SECURITY.md)** - Security implementation details
- **[SECURITY_AUDIT_2025.md](SECURITY_AUDIT_2025.md)** - Security audit procedures
- **[SECURITY_AUDIT_RESULTS_2025_08_25.md](SECURITY_AUDIT_RESULTS_2025_08_25.md)** - Latest audit results (Aug 25, 2025)
- **[BACKUP_SECURITY.md](BACKUP_SECURITY.md)** - Backup system architecture
- **[BACKUP_SETUP.md](BACKUP_SETUP.md)** - Backup configuration guide
- **[RENDER_MCP_SECURITY.md](RENDER_MCP_SECURITY.md)** - MCP Server security safeguards

## 🛠️ Configuration Files

### Backend
- **backend/requirements.txt** - Python dependencies
- **backend/alembic.ini** - Database migration config
- **backend/build_starter.sh** - Render build script
- **backend/start_render.sh** - Render startup script
- **.env.example** - Environment variable template

### Frontend
- **frontend/package.json** - Node dependencies
- **frontend/vite.config.ts** - Vite configuration
- **frontend/tsconfig.json** - TypeScript configuration
- **frontend/vercel.json** - Vercel deployment config

### CI/CD
- **.github/workflows/** - GitHub Actions workflows
- **.pre-commit-config.yaml** - Pre-commit hooks
- **.gitignore** - Git ignore patterns

## 📂 Project Structure

```
project/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── tests/        # Test suites
│   └── scripts/      # Utility scripts
├── frontend/         # React frontend
│   ├── src/          # Source code
│   ├── tests/        # Test suites
│   └── dist/         # Build output
├── scripts/          # Project-wide scripts
└── docs/             # Additional documentation
```

## 🔑 Key Information

### Current Infrastructure
- **Backend**: Render Starter ($7/month)
- **Frontend**: Vercel (free tier)
- **Database**: PostgreSQL Basic-256mb ($6/month)
- **Domain**: aistudyarchitect.com
- **Backups**: R2 (daily) + S3 (weekly)

### Critical Environment Variables
- **Must Backup**: `BACKUP_ENCRYPTION_KEY` (in password manager)
- **Recoverable**: All API keys (can regenerate)
- **Auto-managed**: `DATABASE_URL` (by Render)

### Quick Commands
```bash
# Local development
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# Testing
cd backend && pytest tests/
cd frontend && npm test

# Deployment (automatic on push)
git push origin main
```

## 📝 Documentation Updates

### Latest Changes (2025-08-24)
- Consolidated deployment docs into DEPLOYMENT.md
- Created DEVELOPMENT.md for developer guide
- Cleaned up redundant files
- Fixed double scrollbar in Study Materials panel
- Fixed FAB badge counting issue during streaming

### Maintenance Schedule
- **Weekly**: Review error logs
- **Monthly**: Test backup restoration
- **Quarterly**: Rotate API keys
- **Yearly**: Security audit

## 🚀 Quick Start Guides

### For New Developers
1. Read [DEVELOPMENT.md](DEVELOPMENT.md)
2. Review [CLAUDE.md](CLAUDE.md)
3. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### For Operations
1. Read [DEPLOYMENT.md](DEPLOYMENT.md)
2. Review [BACKUP_SETUP.md](BACKUP_SETUP.md)
3. Check monitoring dashboards

### For Security Review
1. Read [SECURITY.md](SECURITY.md)
2. Review [SECURITY_ASSESSMENT_2025.md](SECURITY_ASSESSMENT_2025.md)
3. Check [RENDER_MCP_SECURITY.md](RENDER_MCP_SECURITY.md)

## 📞 Support

- **GitHub Issues**: https://github.com/belumume/ai-study-architect/issues
- **API Docs**: https://ai-study-architect.onrender.com/docs
- **Live App**: https://aistudyarchitect.com