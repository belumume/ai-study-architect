# Render Dashboard Settings

**IMPORTANT**: These settings must be configured in the Render dashboard and kept in sync with this file.
Last updated: 2025-08-08

## Required Settings (Cannot be blank)

### Root Directory
```
project/backend
```

### Build Command
```
chmod +x build_starter.sh && ./build_starter.sh
```
- For Starter plan ($7/month) - attempts PostgreSQL 17 installation
- Falls back gracefully if permissions insufficient
- Installs Python dependencies
- Sets up RSA keys for JWT

### Pre-Deploy Command
```
# MUST BE EMPTY - DO NOT ADD ANYTHING HERE
```
- **IMPORTANT**: Leave this field completely empty in Render dashboard
- Database already has tables from before Alembic was added
- Any migration command here will fail with "table already exists"
- Migrations are handled safely in start_render.sh instead

### Start Command  
```
chmod +x start_render.sh && ./start_render.sh
```
- **IMPORTANT: Use start_render.sh which has error handling**
- Handles migrations safely (skips if tables exist)
- Provides debugging output
- Works with existing database

## Why Dashboard Settings + Documentation?

1. **Render requires** Build and Start commands (cannot be blank)
2. **render.yaml alone isn't enough** - dashboard settings override it
3. **This file is the source of truth** - update here first, then dashboard

## When to Update

Update both this file AND Render dashboard when:
- Changing PostgreSQL version
- Modifying build process
- Changing startup sequence

## Verification

After any changes:
1. Check this file matches dashboard
2. Trigger manual deploy
3. Check build logs for PostgreSQL 17 confirmation: `pg_dump (PostgreSQL) 17`

## Current Status
- ✅ PostgreSQL 17 client installation configured
- ✅ Build script handles all dependencies
- ✅ Start script handles migrations and server startup