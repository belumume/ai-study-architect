# Cloudflare Migration Design

**Date**: 2026-03-12
**Status**: Approved
**Scope**: Migrate Study Architect backend from deleted Render infrastructure to Cloudflare Containers + Neon PostgreSQL + R2 storage. Remove LangChain dependency.

## Context

Render web service and PostgreSQL database were deleted (suspended since Aug 2025, unpaid invoices). S3 backups preserved but contain minimal test data. Frontend on Vercel still works. Cloudflare Worker routes `/api/*` to dead Render URL. Cloudflare startup credits ($5k, expires Mar 2027) available.

Decision: fresh database, no data restoration. Optimize for long-term engineering durability, zero vendor lock-in, standard protocols at every boundary.

## Architecture

### Layers

| Layer | Service | Protocol | Portable To |
|-------|---------|----------|-------------|
| Frontend | Vercel (React + Vite) | HTTPS | Any static host |
| Edge | CF Worker + DNS | HTTPS | Any reverse proxy |
| Compute | CF Container (Docker) | HTTPS | Any container host (Fly.io, Cloud Run, ECS) |
| Database | Neon PostgreSQL | PG wire protocol | Any PG provider or self-hosted |
| Storage | R2 | S3 API | AWS S3, MinIO, Backblaze B2 |
| Cache | Upstash Redis | Redis protocol (HTTPS REST) | Any Redis provider or self-hosted |
| AI APIs | Anthropic (primary), OpenAI (fallback) | HTTPS | N/A (external services) |

### Request Flow

```
Browser
  -> aistudyarchitect.com (CF DNS)
  -> Vercel (static assets, SPA)
  -> CF Worker (/api/* routes)
    -> CF Container (FastAPI + Uvicorn)
      -> Neon PostgreSQL (via pooled connection string)
      -> R2 (file uploads, backups)
      -> Anthropic / OpenAI APIs (AI responses)
```

### Design Properties

- **Zero vendor lock-in**: Docker + standard PostgreSQL + S3 API. Every component replaceable independently.
- **Scale to zero**: Container sleeps when idle (pay-per-use). Neon auto-suspends after 5 min idle.
- **Standard protocols**: HTTPS, PG wire protocol, S3 API. No proprietary glue between layers.
- **Portable artifacts**: Dockerfile, Alembic migrations, pytest/vitest suites all work on any platform.

## Component Details

### 1. Compute -- CF Container

**Instance**: `basic` (1/4 vCPU, 1 GiB RAM, 4 GB disk). Sufficient for single-user workload, scales up without code changes.

**Dockerfile** (new, replaces `Dockerfile.render`):

```dockerfile
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python scripts/generate_rsa_keys.py || echo "RSA keys generation skipped"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Changes from `Dockerfile.render`:
- Remove PostgreSQL 17 client install (no more `pg_dump` from container; backups run from CI)
- Remove Render-specific path fixes (`fix_alembic_state.py`)
- Remove `start_render.sh` / `build.sh` indirection
- Keep `libmagic1` for python-magic file type detection
- Keep RSA key generation for JWT

**Worker routing** (`wrangler.toml` configures both Worker and Container):

The Worker is a small TypeScript entry point (`worker/index.ts`) built by wrangler as part of `wrangler deploy`. The Worker project includes its own `package.json` with `wrangler` as a dev dependency. No separate build pipeline -- wrangler handles TypeScript compilation internally.

The Worker:
- Proxies `/api/*` to the Container (replacing dead Render URL)
- Blocks `/api/docs`, `/api/openapi.json`, `/api/redoc` (existing security policy)
- Passes through CORS preflight at edge
- Wakes container on first request after sleep

**Container sleep**: Auto-sleep after idle timeout (configurable, default ~5 min). Cold start on wake is ~2-5s. Acceptable for low-traffic single-user app. Frontend can show a loading indicator during wake.

**Compound cold start warning**: If both the Container AND Neon compute are cold simultaneously (both idle >5 min), the first request may take ~5-8s (container wake + Neon compute wake). This is acceptable for single-user. Mitigations if needed: cron ping to keep container warm, or Neon's "always on" compute option on paid plans.

### 2. Database -- Neon PostgreSQL

**Why Neon**: Serverless PostgreSQL with auto-suspend, standard PG wire protocol, free tier sufficient for current usage (100 CU-hours/month, 0.5 GB storage). No BaaS overhead (unlike Supabase -- we don't need bundled auth/storage/realtime).

**Connection**:
- Use Neon's built-in connection pooler (PgBouncer in transaction mode) -- provides a pooled `postgresql://` connection string
- Driver: `psycopg2-binary` (standardize, remove `pg8000`). Using `-binary` is intentional for container deployment (no system libpq needed).
- Hyperdrive reserved for future Worker-level DB access if needed

**Connection pool tuning for Neon**:
- Reduce `DB_POOL_SIZE` from 20 to 5 (Neon PgBouncer has its own pooling; large app-side pools can exhaust connections on wake)
- Keep `DB_POOL_PRE_PING=True` (critical for serverless -- detects stale connections after Neon auto-suspend)
- Keep `DB_POOL_RECYCLE=3600` (recycle connections hourly)

**Migration**:
- Fresh database, run `alembic upgrade head` as part of deploy pipeline
- All 5 existing Alembic migrations apply unchanged
- 8 SQLAlchemy model classes across 6 files unchanged (User, Content, StudySession, PracticeSession, Problem, Concept, ConceptDependency, ChatMessage)

**Config changes** (`config.py`):
- `DATABASE_URL` env var points to Neon pooled connection string
- Remove `postgres://` -> `postgresql://` Render rewrite
- Remove `pg8000` driver path in `DATABASE_URL_SQLALCHEMY` property
- Simplify to: if `DATABASE_URL` is set, use it (with `psycopg2` driver); else construct from `POSTGRES_*` vars for local dev
- Reduce `DB_POOL_SIZE` default from 20 to 5

### 3. Storage -- R2

**Bucket**: `study-architect-storage`

**Layout**:
```
study-architect-storage/
  uploads/{user_id}/{filename}    # File uploads (PDF, DOCX, images)
  backups/{date}/backup.sql.gz    # Database backups
```

**Access**: boto3 with R2 endpoint configuration:
```
R2_ENDPOINT_URL=https://{account_id}.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=study-architect-storage
```

**File operations rewrite** (required across `content.py` + `content_processor.py`):

Current flow: `content.py:save_upload_file()` writes bytes to local `uploads/` dir -> saves path in DB -> `ContentProcessor` reads from local disk path -> extracts text. Download serves via `FileResponse(path=...)`. Delete uses `Path.unlink()`.

New flow:
1. **Upload** (`save_upload_file()`): Upload bytes to R2 via boto3 `put_object()`, save R2 key in DB (e.g., `uploads/{user_id}/{uuid}_{filename}`)
2. **Process** (`ContentProcessor.process_file()`): Download from R2 to temp directory (`tempfile.mkdtemp()`), process (text extraction, OCR), clean up temp files
3. **Download** (`download_content`): Generate R2 presigned URL via `generate_presigned_url()` and redirect (offloads bandwidth from container). Alternatively, stream via `boto3.get_object()` + `StreamingResponse` if presigned URLs are not desired.
4. **Delete** (`delete_content`, `bulk_delete_content`): Replace `Path.unlink()` with `s3.delete_object(Bucket=..., Key=...)`
5. Extracted text stored in DB `content.extracted_text` field (unchanged)

**Cleanup**: Remove `UPLOAD_DIR` constant, module-level `mkdir()` call, and `settings.UPLOAD_DIR` config field -- all local disk references eliminated. Remove dead code `self.upload_dir` in `ContentProcessor.__init__`.

This preserves the processing pipeline while eliminating local disk dependency. The temp directory pattern is standard for container workloads with ephemeral storage.

**Backups**: See CI/CD section. Neon also provides built-in point-in-time recovery (6 hours on free tier, 7-30 days on paid) which covers most accidental data loss without any custom backup infrastructure.

### 3b. Cache -- Upstash Redis

**Why Upstash**: The existing `MockRedisClient` is a no-op stub (every `get()` returns `None`, every `set()` returns `True`). It doesn't cache anything. The `RedisCache` and `AIResponseCache` classes are already implemented and functional -- they just need a real backend.

Upstash provides:
- Redis-compatible REST API over HTTPS (no TCP socket needed -- works from both Workers and Containers)
- Free tier: 10k commands/day, 256 MB storage
- Native CF integration (Upstash is a first-party CF integration partner)
- The codebase already has `app/core/upstash_cache.py` with an `UpstashRedisClient` -- this was built but never activated

**What changes**:
- Set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` env vars (the existing `cache.py` already checks for these and activates `UpstashRedisClient` automatically -- lines 33-37)
- Remove `MockRedisClient` class (dead code once Upstash is configured)
- Remove the `redis` package from requirements.txt (Upstash uses REST, not the redis wire protocol)
- Verify `UpstashRedisClient` in `upstash_cache.py` implements the same interface used by `RedisCache._get_client()`

**What stays**: `RedisCache`, `AIResponseCache`, `cached_ai_response` decorator -- all unchanged. These already work with any client that implements `get/set/delete/exists/keys`.

**Result**: AI response caching (24h TTL), embedding caching (7d TTL), and the decorator-based caching all start working immediately. Every repeated query hits cache instead of re-calling Claude/OpenAI.

### 3c. Health Check Enhancement

Add `/health/ready` endpoint that verifies actual service connectivity:

```python
@app.get("/health/ready")
def readiness_check(request: Request):
    db_ok = test_database_connection()  # already exists in database.py
    cache_ok = redis_cache.is_connected
    return {
        "status": "ready" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "cache": "connected" if cache_ok else "disconnected",
    }
```

The deploy pipeline health check uses `/health/ready` instead of `/health` to verify DB connectivity after deploy. The existing `/health` (static response) remains for simple liveness checks.

### 4. AI Service Layer -- LangChain Removal

**Current dependency chain**:
```
langchain 0.3.27
langchain-core 0.3.72
langchain-community 0.3.27
langgraph 0.2.60
  + ~30 transitive dependencies (pydantic compat shims, tenacity, etc.)
```

**Why remove**: LangChain adds abstraction over the Anthropic/OpenAI SDKs without providing value for the current feature set (single Lead Tutor agent with Socratic questioning). The existing `claude_service.py`, `openai_fallback.py`, and `ai_service_manager.py` already call the SDKs directly and handle failover. LangChain sits on top adding indirection, dependency weight, and debugging complexity.

**What stays**:
- `anthropic==0.39.0` -- Claude API integration (primary)
- `openai==1.35.0` -- OpenAI fallback service
- `app/services/claude_service.py` -- direct Anthropic SDK calls with streaming
- `app/services/openai_fallback.py` -- direct OpenAI SDK calls
- `app/services/ai_service_manager.py` -- service selection and failover logic

**What gets removed from `requirements.txt`**:
- `langchain`, `langchain-core`, `langchain-community`, `langgraph`
- `numpy` (no application code imports it; only pulled in by LangChain. Re-add in Phase 2 if needed.)

**Complete list of files with LangChain imports** (audited via grep):

| File | LangChain Usage | Replacement |
|------|----------------|-------------|
| `app/agents/base.py:9` | `from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage` | Plain Python dataclasses or typed dicts for message types |
| `app/agents/lead_tutor.py:9-11` | `HumanMessage, AIMessage`, `ChatPromptTemplate`, `JsonOutputParser` | Direct Anthropic/OpenAI SDK message format, f-string or Jinja templates, `json.loads()` |
| `app/core/agent_manager.py:378` | `from langchain_core.messages import HumanMessage, AIMessage, SystemMessage` | Same plain Python message types from refactored `base.py` |

**Refactoring approach**:
- Define simple message dataclasses in `base.py` (role + content, matching Anthropic/OpenAI SDK format)
- Replace `ChatPromptTemplate` with f-strings or a thin template helper
- Replace `JsonOutputParser` with `json.loads()` on SDK response content
- Preserve identical external behavior (Socratic questioning, streaming, context management)
- All existing tests must pass after refactoring

**Future-proofing**: If Phase 2 (knowledge graph, practice generation, multi-agent orchestration) needs an orchestration framework, evaluate LangGraph or a lightweight custom solution at that time -- as a deliberate addition, not a legacy dependency carried forward.

### 5. CI/CD Pipeline

**Workflows**:

#### `deploy.yml` (new)
```yaml
on:
  push:
    branches: [main]

jobs:
  test:
    # Run pytest (backend) + vitest (frontend)
    # Same as current staging.yml test job

  migrate:
    needs: test
    steps:
      - Install Python + psycopg2-binary
      - Run: alembic upgrade head (against NEON_DATABASE_URL)
      # Runs migrations before deploying new code
      # Idempotent: no-op if already at head

  deploy:
    needs: migrate
    steps:
      - npm install (wrangler)
      - wrangler deploy (pushes Container + Worker)
      - Health check: curl /api/v1/health (verify DB connectivity)
```

#### `staging.yml` (rewrite)
```yaml
on:
  push:
    branches: [develop, staging]
  pull_request:
    branches: [main]

jobs:
  test:
    # pytest + vitest (unchanged)

  deploy-staging:
    # wrangler deploy --env staging (replaces Render API call)
```

#### `backup.yml` (rewrite)
```yaml
on:
  schedule:
    - cron: '0 2 * * *'     # Daily R2
    - cron: '0 3 * * 0'     # Weekly S3

jobs:
  backup:
    steps:
      - Install postgresql-client
      - pg_dump against Neon connection string
      - Compress: gzip
      - Upload to R2 (daily) and/or S3 (weekly)
```

#### `claude.yml`, `claude-code-review.yml` -- unchanged

**GitHub Secrets** (new):
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `NEON_DATABASE_URL` (for migrations + backup pg_dump)
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`

**GitHub Secrets** (remove):
- `RENDER_API_KEY`
- `STAGING_SERVICE_ID`
- `BACKUP_TOKEN`

### 6. Configuration & Security

**Environment variables** (Container):

| Variable | Source | Notes |
|----------|--------|-------|
| `DATABASE_URL` | Neon pooled connection string | Standard `postgresql://` format |
| `JWT_SECRET_KEY` | Generated secret | Fresh DB = new keys OK |
| `JWT_ALGORITHM` | `RS256` | Unchanged |
| `SECRET_KEY` | Generated secret | CSRF/session signing |
| `ANTHROPIC_API_KEY` | Anthropic console | Primary AI |
| `OPENAI_API_KEY` | OpenAI platform | Fallback AI |
| `R2_ENDPOINT_URL` | CF dashboard | R2 S3-compatible endpoint |
| `R2_ACCESS_KEY_ID` | CF dashboard | R2 access credentials |
| `R2_SECRET_ACCESS_KEY` | CF dashboard | R2 secret credentials |
| `R2_BUCKET_NAME` | `study-architect-storage` | Single bucket |
| `UPSTASH_REDIS_REST_URL` | Upstash console | Redis cache endpoint |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash console | Redis cache auth token |
| `BACKEND_CORS_ORIGINS` | Vercel domains | Unchanged |
| `ENVIRONMENT` | `production` | Unchanged |

**`main.py` cleanup**:
- Delete the entire path-setup block (lines 6-29): the `_path_setup` import chain with Render path fallbacks. In a Docker container, `WORKDIR /app` handles paths.
- Update `TrustedHostMiddleware` allowed hosts:
  - Remove: `ai-study-architect.onrender.com`, `*.onrender.com`
  - Keep: `localhost`, `127.0.0.1`, `aistudyarchitect.com`, `www.aistudyarchitect.com`, `api.aistudyarchitect.com`
  - Add: CF Container hostname (if different from the above)

**`mypy` config**: Remove `[mypy-langchain.*]` and `[mypy-langgraph.*]` ignore sections.

**CORS**: Unchanged -- already configured for Vercel frontend domains.

## Files Changed

### Modified
- `backend/app/core/config.py` -- Neon URL handling, remove Render rewrites, remove pg8000 path, reduce pool size to 5
- `backend/app/main.py` -- Delete Render path-setup block (lines 6-29), update TrustedHostMiddleware hosts
- `backend/requirements.txt` -- Remove langchain (4 packages), numpy, pg8000, redis; keep boto3 (already present)
- `backend/app/agents/base.py` -- Replace `langchain_core.messages` imports with plain Python message types
- `backend/app/agents/lead_tutor.py` -- Replace `langchain_core` imports (messages, prompts, parsers) with direct SDK calls
- `backend/app/core/agent_manager.py` -- Replace `langchain_core.messages` import (line 378) with refactored message types
- `backend/app/api/v1/content.py` -- Rewrite `save_upload_file()` to upload to R2 via boto3, remove `UPLOAD_DIR` local disk logic
- `backend/app/services/content_processor.py` -- Download from R2 to temp dir for processing, clean up after, remove dead `self.upload_dir`
- `backend/app/core/cache.py` -- Remove `MockRedisClient` class (dead code with Upstash active)
- `backend/app/main.py` -- Add `/health/ready` endpoint with DB + cache connectivity check
- `.github/workflows/backup.yml` -- pg_dump Neon -> R2/S3 upload
- `.github/workflows/staging.yml` -- wrangler deploy instead of Render API
- `backend/app/core/config.py` -- Remove `UPLOAD_DIR` setting (no longer used with R2)
- `backend/tests/scripts/test_requirements.py` -- Remove hardcoded LangChain package references
- `mypy.ini` (or equivalent) -- Remove langchain/langgraph ignore sections

### Removed
- `backend/Dockerfile.render`
- `backend/render.yaml`
- `backend/render-crons.yaml`
- `backend/build.sh`
- `backend/start_render.sh`
- `backend/app/_path_setup.py` (Render path hack)

### New
- `backend/Dockerfile` -- Clean container build
- `wrangler.toml` -- CF Container + Worker configuration
- `worker/package.json` -- Wrangler dev dependency for Worker build
- `worker/index.ts` -- CF Worker entry point (routes /api/* to Container)
- `.github/workflows/deploy.yml` -- Production CI/CD pipeline (test -> migrate -> deploy)

## Execution Order

1. **Neon setup**: Create Neon project, get pooled connection string
2. **R2 setup**: Create R2 bucket `study-architect-storage`, generate API credentials
3. **Upstash setup**: Create Upstash Redis database via CF integration, get REST URL + token
3b. **Alembic migration**: Run `alembic upgrade head` against Neon (creates all tables)
4. **LangChain removal**: Refactor agent code, remove packages, update `test_requirements.py`, verify tests pass
5. **File upload rewrite**: Update content.py + content_processor.py for R2
6. **Dockerfile**: Write clean Dockerfile, test local build
7. **Worker**: Write Worker entry point + wrangler.toml, test locally with `wrangler dev`
8. **Deploy**: `wrangler deploy` -- pushes Container + Worker to CF
9. **CF Worker routing update**: Update existing aistudyarchitect.com Worker to route /api/* to Container (or replace it with the new Worker)
10. **CI/CD**: Write deploy.yml, rewrite staging.yml + backup.yml
11. **Cleanup**: Remove Render artifacts, update CLAUDE.md, update project memory
12. **Verify**: Health check, run full test suite against deployed endpoint, test file upload + AI chat end-to-end

## Rollback Strategy

Render is deleted -- there is no rollback to previous infrastructure. Rollback options:

| Scenario | Action |
|----------|--------|
| CF Container deploy fails | Fix and redeploy. App is not live anyway (currently dead). No user impact. |
| CF Container has runtime issues post-deploy | Docker image is portable. Deploy same image to Fly.io (`fly deploy`) or Cloud Run (`gcloud run deploy`) with zero code changes. Update Worker routing to point at new host. |
| Neon outage | Neon provides 99.95% SLA on paid plans. On free tier, accept the risk. Backups in R2/S3 allow restore to any PG provider. |
| LangChain removal breaks agent behavior | Tests catch regressions before deploy. If missed: revert the agent refactor commits (git revert), re-add langchain to requirements.txt, redeploy. Agent code is isolated in `app/agents/`. |
| Everything fails | Fall back to local development only (uvicorn + local PG) until infrastructure is resolved. No user-facing commitment exists. |

## Cost Estimate

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| CF Workers Paid | $5 | Base plan, includes Container allowances |
| CF Container overflow | ~$2-5 | Basic instance, ~4 hrs active/day |
| Neon PostgreSQL | $0 | Free tier (100 CU-hours, 0.5 GB) |
| R2 Storage | $0 | 10 GB free, minimal usage |
| Upstash Redis | $0 | Free tier (10k commands/day, 256 MB) |
| Vercel | $0 | Free tier (hobby) |
| Network egress | $0 | 1 TB included, minimal traffic |
| **Total** | **~$7-10/mo** | **Covered by $5k CF credits through Mar 2027** |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CF Containers is newer than Cloud Run/ECS | Less community knowledge, potential edge cases | Docker-based = portable. If issues arise, migrate Container to Fly.io/Cloud Run with zero code changes. |
| Compound cold start (Container + Neon both cold) | First request after ~5 min idle could take 5-8s | Frontend loading indicator. Cron ping to keep warm. Neon "always on" on paid plan if needed. |
| Neon free tier limits (100 CU-hours) | May hit limits under sustained usage | Monitor usage. Scale plan ($19/mo) still covered by credits. |
| LangChain removal breaks agent code | Agent behavior regression | Complete import audit done (3 files identified). All existing tests must pass. Revert path is simple (git revert + re-add package). |
| R2/boto3 compatibility edge cases | File upload failures | R2 is S3-compatible; boto3 is the standard client. Test upload/download in staging before production. |

## Out of Scope

- Frontend changes (Vercel deployment unchanged)
- New features (analytics dashboard, knowledge graph -- Phase 2)
- Hyperdrive setup (reserve for Worker-level DB access if needed)
- Database data migration (fresh start confirmed)

## References

- [CF Containers Pricing](https://developers.cloudflare.com/containers/pricing/)
- [CF Workers Python Support](https://developers.cloudflare.com/workers/languages/python/)
- [FastAPI on CF Containers (example repo)](https://github.com/abyesilyurt/fastapi-on-cloudflare-containers)
- [Neon + Cloudflare Hyperdrive](https://neon.com/docs/guides/cloudflare-hyperdrive)
- [Neon Pricing 2026](https://neon.com/pricing)
- [Python Workers Advancements (blog)](https://blog.cloudflare.com/python-workers-advancements/)
- [Best PostgreSQL Hosting 2026](https://dev.to/philip_mcclarence_2ef9475/best-postgresql-hosting-in-2026-rds-vs-supabase-vs-neon-vs-self-hosted-5fkp)
