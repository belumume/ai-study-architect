# RENDER DASHBOARD SETTINGS
**IMPORTANT: These settings MUST be configured in Render Dashboard**
Last Updated: 2025-08-08

## Build & Deploy Settings

### Root Directory
```
project/backend
```

### Build Command
```bash
chmod +x build.sh && ./build.sh
```

### Start Command  
```bash
chmod +x start_render.sh && ./start_render.sh
```

## Why Dashboard Settings?
- Single source of truth that's immediately visible
- No confusion about which config takes precedence
- Render.yaml becomes documentation/backup only
- Changes require conscious action in dashboard

## What Each Script Does

### build.sh
- Installs PostgreSQL 17 client (matches database version)
- Installs Python dependencies
- Sets up RSA keys for JWT

### start_render.sh
- Sets up Python path
- Runs database migrations
- Starts FastAPI server on correct port

## Environment Variables (Set in Dashboard)
- `DATABASE_URL` - From database connection
- `ANTHROPIC_API_KEY` - Your Claude API key
- `OPENAI_API_KEY` - OpenAI fallback key
- `BACKUP_TOKEN` - For backup authentication
- `AWS_ACCESS_KEY_ID` - For S3 backups
- `AWS_SECRET_ACCESS_KEY` - For S3 backups
- `BACKUP_ENCRYPTION_KEY` - For encrypted backups

## Verification
After any changes, verify in dashboard that:
1. Build command includes `build.sh`
2. Start command includes `start_render.sh`
3. Root directory is `project/backend`

---
⚠️ **DO NOT rely on render.yaml for these settings** - Dashboard takes precedence!