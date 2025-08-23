# Documentation Index

## Core Documentation

### Project Overview
- **README.md** - Main project introduction and features
- **CLAUDE.md** - AI assistant guidelines and development commands
- **CLAUDE.local.md** - Private local instructions (not in git)

### Security & Backup
- **SECURITY.md** - Security implementation details
- **BACKUP_SECURITY.md** - Backup system security architecture
- **BACKUP_SETUP.md** - Backup configuration guide
- **RENDER_MCP_SECURITY.md** - MCP Server security safeguards ⚠️ NEW

### Infrastructure & Deployment
- **PRODUCTION_NOTES.md** - Production deployment details
- **TROUBLESHOOTING.md** - Comprehensive troubleshooting guide ⚠️ NEW
- **vercel.json** - Frontend routing configuration

## Scripts Documentation

### Backup & Recovery Scripts
- **scripts/backup_env_vars.py** - Environment variable backup script
- **scripts/secure_backup_options.py** - Multiple backup strategies
- **scripts/env_vars_criticality_analysis.md** - Analysis of which env vars need backup ⚠️ IMPORTANT
- **scripts/proton_pass_backup_guide.md** - Guide for Proton Pass backup

### Deployment Scripts
- **backend/build_starter.sh** - Render build script
- **backend/start_render.sh** - Render startup script
- **scripts/tag_version.sh** - Version tagging utility

## Key Insights from Latest Updates

### Environment Variables
- **CRITICAL**: Only `BACKUP_ENCRYPTION_KEY` truly needs backup (stored in Proton Pass)
- **Recoverable**: All API keys can be regenerated in minutes
- **Auto-managed**: DATABASE_URL is managed by Render

### MCP Server Setup
- **Installed**: Render MCP Server via Claude Code
- **Safe Operations**: list_services, list_logs, get_metrics
- **Dangerous Operations**: update_environment_variables (use with extreme caution)
- **Security**: See RENDER_MCP_SECURITY.md for safeguards

### Current Infrastructure
- **Backend**: Render Starter ($7/month) - https://ai-study-architect.onrender.com
- **Frontend**: Vercel (free tier) - Same URL via proxy
- **Database**: PostgreSQL Basic-256mb ($6/month, expires Sept 6, 2025)
- **Backups**: Dual-provider (R2 daily, S3 weekly)

## Quick Reference Paths

### For Development
1. Start here: **CLAUDE.md** (commands and setup)
2. Security concerns: **RENDER_MCP_SECURITY.md**
3. Deployment issues: **PRODUCTION_NOTES.md**

### For Backup/Recovery
1. What needs backup: **scripts/env_vars_criticality_analysis.md**
2. How to backup: **scripts/proton_pass_backup_guide.md**
3. Backup system: **BACKUP_SECURITY.md**

### For New Contributors
1. Project overview: **README.md**
2. Development setup: **CLAUDE.md**
3. Security practices: **SECURITY.md**

## Documentation Maintenance

Last comprehensive review: 2025-08-23
- Added MCP Server documentation
- Clarified environment variable criticality
- Updated deployment URLs
- Removed reference to non-existent RENDER_SETTINGS.md
- Added comprehensive TROUBLESHOOTING.md guide
- Documented streaming and API key loading fixes

## Notes

- Frontend deployment is on Vercel, not Render (common confusion point)
- Pre-Deploy command in Render MUST be empty
- Windows PostgreSQL uses port 5433 (not 5432)
- Redis/Upstash removed - using MockRedisClient fallback