# Cloudflare Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Study Architect backend from deleted Render to CF Containers + Neon PostgreSQL + R2 + Upstash Redis, removing LangChain dependency.

**Architecture:** Docker container on CF Containers running FastAPI + Uvicorn. Neon serverless PostgreSQL via pooled connection. R2 for file storage/backups (S3-compatible). Upstash Redis for caching (REST API). CF Worker at edge for /api/* routing. Vercel frontend unchanged.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, psycopg2-binary, boto3, anthropic SDK, openai SDK, wrangler CLI, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-03-12-cloudflare-migration-design.md`

---

## Chunk 1: Infrastructure Setup + LangChain Removal

### Task 1: External Service Setup (manual steps)

These are manual setup steps done in browser dashboards before any code changes.

**Files:** None (external services)

- [ ] **Step 1: Create Neon PostgreSQL project**

Go to https://console.neon.tech. Create a new project:
- Project name: `study-architect`
- Region: `us-east-1` (closest to CF edge)
- PostgreSQL version: 17

Copy the **pooled** connection string (the one with `-pooler` in the hostname). It looks like:
```
postgresql://user:password@ep-xxxxx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
```

Save this as `NEON_DATABASE_URL` for later steps.

- [ ] **Step 2: Create R2 bucket**

Go to CF dashboard > R2 > Create bucket:
- Bucket name: `study-architect-storage`
- Location: Automatic

Then go to R2 > Manage R2 API Tokens > Create API token:
- Permissions: Object Read & Write
- Specify bucket: `study-architect-storage`

Save `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, and the account ID for `R2_ENDPOINT_URL` (`https://{account_id}.r2.cloudflarestorage.com`).

- [ ] **Step 3: Create Upstash Redis database**

Go to CF dashboard > Workers & Pages > Upstash (or https://console.upstash.com):
- Database name: `study-architect-cache`
- Region: `us-east-1`
- Type: Regional

Copy `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.

- [ ] **Step 4: Run Alembic migrations against Neon**

```bash
cd backend
# Set the DATABASE_URL temporarily for migration
export DATABASE_URL="postgresql+psycopg2://user:password@ep-xxxxx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
alembic upgrade head
```

Expected: 5 migrations applied, all tables created. Verify:
```bash
python -c "
from sqlalchemy import create_engine, inspect
import os
engine = create_engine(os.environ['DATABASE_URL'])
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Tables: {len(tables)}')
for t in sorted(tables):
    print(f'  {t}')
"
```

Expected output: tables including `users`, `content`, `study_sessions`, `practice_problems`, `chat_messages`, `concepts`, `concept_dependencies`, plus `alembic_version`.

- [ ] **Step 5: Commit — no code changes yet, just verify infra**

No commit needed. Proceed to Task 2.

---

### Task 2: LangChain Removal — Message Types

Replace LangChain message types with plain Python dataclasses in `base.py`. This is the foundation that `lead_tutor.py` and `agent_manager.py` depend on.

**Files:**
- Modify: `backend/app/agents/base.py`
- Test: `backend/tests/` (existing agent tests)

- [ ] **Step 1: Run existing tests to establish baseline**

```bash
cd backend
pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: 133 tests passing. Note exact count.

- [ ] **Step 2: Replace LangChain message imports in base.py**

Replace line 9:
```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
```

With plain Python dataclasses:
```python
from dataclasses import dataclass, field


@dataclass
class BaseMessage:
    content: str
    role: str = ""

    def dict(self) -> dict:
        return {"content": self.content, "role": self.role}

@dataclass
class HumanMessage(BaseMessage):
    role: str = field(default="user", init=False)

@dataclass
class AIMessage(BaseMessage):
    role: str = field(default="assistant", init=False)

@dataclass
class SystemMessage(BaseMessage):
    role: str = field(default="system", init=False)
```

These dataclasses match the interface used throughout the codebase: `.content` attribute and role identification via class type or `.role` attribute. They also match the Anthropic/OpenAI SDK message format (`{"role": "...", "content": "..."}`).

- [ ] **Step 3: Run tests to verify nothing broke**

```bash
cd backend
pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: Same number of tests passing as Step 1.

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/base.py
git commit -m "refactor: replace LangChain message types with plain dataclasses

Removes langchain_core.messages dependency from base agent.
HumanMessage, AIMessage, SystemMessage are now simple dataclasses
matching the Anthropic/OpenAI SDK message format."
```

---

### Task 3: LangChain Removal — Lead Tutor Agent

Remove LangChain imports from `lead_tutor.py`: `ChatPromptTemplate`, `JsonOutputParser`, and message types.

**Files:**
- Modify: `backend/app/agents/lead_tutor.py`
- Test: `backend/tests/` (existing agent tests)

- [ ] **Step 1: Replace imports (lines 9-11)**

Remove:
```python
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
```

Replace with:
```python
import json as json_module
from app.agents.base import HumanMessage, AIMessage
```

- [ ] **Step 2: Remove JsonOutputParser from __init__ (line 52)**

Remove:
```python
        self.json_parser = JsonOutputParser()
```

- [ ] **Step 3: Replace ChatPromptTemplate in _create_study_plan (lines 113-154)**

Replace the `ChatPromptTemplate.from_messages` block and `plan_prompt.format_messages` call with a direct f-string:

```python
    def _create_study_plan(self, user_input: str, context: Dict[str, Any]) -> AgentResponse:
        """Create a personalized study plan based on student goals"""

        knowledge_level = context.get("knowledge_level", "beginner")
        time_available = context.get("time_available", "flexible")
        learning_style = context.get("learning_style", self.tutor_state.learning_style or "visual")

        plan_prompt = f"""{self.get_system_prompt()}

Based on the following learning goal, create a detailed study plan:

Goal: {user_input}
Current Knowledge Level: {knowledge_level}
Available Time: {time_available}
Learning Style: {learning_style}

Please provide a structured study plan with:
1. Clear learning objectives (3-5 main objectives)
2. Recommended sequence of topics
3. Estimated time for each section
4. Suggested resources and practice methods
5. Milestones to track progress

Format your response as a JSON object with the following structure:
{{
    "title": "Study plan title",
    "description": "Brief overview of the plan",
    "total_hours": estimated total hours,
    "objectives": [
        {{
            "id": "obj1",
            "title": "Objective title",
            "description": "What the student will learn",
            "estimated_hours": hours,
            "topics": ["topic1", "topic2"],
            "prerequisites": ["prereq1"],
            "resources": ["resource1", "resource2"]
        }}
    ],
    "milestones": [
        {{
            "title": "Milestone title",
            "description": "What indicates this milestone is reached",
            "objectives_required": ["obj1", "obj2"]
        }}
    ],
    "recommendations": ["recommendation1", "recommendation2"]
}}"""

        response = self.invoke_llm(plan_prompt)
```

- [ ] **Step 4: Replace json_parser.parse calls with json_module.loads**

In `_create_study_plan` (line 176), replace:
```python
            plan_data = self.json_parser.parse(response)
```
With:
```python
            plan_data = json_module.loads(response)
```

In `_check_understanding` (line 324), replace:
```python
            questions_data = self.json_parser.parse(response)
```
With:
```python
            questions_data = json_module.loads(response)
```

Note: `json_module.loads` may fail if the LLM response contains markdown code fences. Add a helper to strip them:

```python
def _parse_json_response(self, response: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = response.strip()
    if text.startswith("```"):
        # Remove opening fence (e.g. ```json)
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
        # Remove closing fence
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return json_module.loads(text)
```

Use `self._parse_json_response(response)` in both places.

- [ ] **Step 5: Run tests**

```bash
cd backend
pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: All tests passing.

- [ ] **Step 6: Commit**

```bash
git add backend/app/agents/lead_tutor.py
git commit -m "refactor: remove LangChain from lead tutor agent

Replace ChatPromptTemplate with f-strings.
Replace JsonOutputParser with json.loads + markdown fence stripping.
Import message types from base.py instead of langchain_core."
```

---

### Task 4: LangChain Removal — Agent Manager + Cleanup

Remove the last LangChain import from `agent_manager.py` and clean up `requirements.txt`.

**Files:**
- Modify: `backend/app/core/agent_manager.py:378`
- Modify: `backend/requirements.txt`
- Modify: `backend/tests/scripts/test_requirements.py` (if it references LangChain)
- Test: `backend/tests/`

- [ ] **Step 1: Fix agent_manager.py import (line 378)**

Replace:
```python
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
```
With:
```python
            from app.agents.base import HumanMessage, AIMessage, SystemMessage
```

- [ ] **Step 2: Update requirements.txt**

Remove these lines:
```
langchain==0.3.27
langchain-core==0.3.72
langchain-community==0.3.27
langgraph==0.2.60
numpy==1.26.3  # Last version compatible with Python 3.12
pg8000==1.31.2
```

**Do NOT remove `redis` or `types-redis` yet** — `cache.py` still imports `redis` at module level. That cleanup happens atomically in Task 6.

Add `requests` as an explicit dependency (currently a transitive dep of LangChain, needed by `upstash_cache.py`):
```
requests==2.31.0
```

Update the comment on psycopg2-binary:
```
# Database
sqlalchemy==2.0.35
alembic==1.13.1
psycopg2-binary==2.9.9
```

Remove the `# Database (using pg8000 for Windows compatibility)` comment and the `# For Render deployment` comment on psycopg2-binary.

Remove the `# Vector store and embeddings` section header (numpy was the only entry).

- [ ] **Step 2b: Fix agent_manager.py model_name references**

Lines 328 and 373 reference `agent.model_name` which doesn't exist on `BaseAgent` (it's `model_preference`). Fix:
- Line 328: change `agent.model_name` to `agent.model_preference`
- Line 373: change `model_name=agent_data.get("model_name", "llama3.2")` to `model_preference=agent_data.get("model_preference", "claude")`

- [ ] **Step 2c: Clean up mypy.ini**

Remove LangChain/LangGraph ignore sections from `backend/mypy.ini` (lines 32-36):
```ini
[mypy-langchain.*]
ignore_missing_imports = True

[mypy-langgraph.*]
ignore_missing_imports = True
```

Also update `python_version = 3.11` to `python_version = 3.12` to match the Dockerfile.

- [ ] **Step 3: Update test_requirements.py if it references LangChain**

```bash
cd backend
grep -n "langchain\|langgraph\|pg8000\|redis" tests/scripts/test_requirements.py
```

Remove any hardcoded references to the removed packages.

- [ ] **Step 4: Run full test suite**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: All 133 backend tests passing.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/agent_manager.py backend/requirements.txt backend/tests/scripts/test_requirements.py
git commit -m "refactor: complete LangChain removal

Remove langchain, langchain-core, langchain-community, langgraph,
numpy, pg8000, redis from requirements.txt.
Standardize on psycopg2-binary for all environments.
~30 transitive dependencies eliminated."
```

---

### Task 5: Config + Main.py Cleanup

Update `config.py` for Neon and `main.py` to remove Render artifacts.

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/`

- [ ] **Step 1: Simplify DATABASE_URL_SQLALCHEMY in config.py**

Replace the entire `DATABASE_URL_SQLALCHEMY` property (lines 106-127) with:

```python
    @property
    def DATABASE_URL_SQLALCHEMY(self) -> str:
        """Get the DATABASE_URL for SQLAlchemy."""
        if os.getenv("DATABASE_URL"):
            db_url = os.getenv("DATABASE_URL")
            # Normalize protocol prefix
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            # Ensure psycopg2 driver
            if "postgresql://" in db_url and "+psycopg2" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return db_url

        if self.POSTGRES_PASSWORD and self.POSTGRES_USER:
            encoded_password = quote_plus(self.POSTGRES_PASSWORD)
            encoded_user = quote_plus(self.POSTGRES_USER)
            return f"postgresql+psycopg2://{encoded_user}:{encoded_password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

        raise ValueError("No database configuration found. Set DATABASE_URL or POSTGRES_* environment variables.")
```

- [ ] **Step 2: Reduce DB_POOL_SIZE default**

Change line 45:
```python
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
```
To:
```python
    DB_POOL_SIZE: int = Field(default=5, description="Database connection pool size")
```

- [ ] **Step 3: Add R2 config fields to Settings**

Add after the `UPLOAD_DIR` field (line 83):
```python
    # R2 Storage
    R2_ENDPOINT_URL: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: str = "study-architect-storage"
```

- [ ] **Step 4: Clean up main.py path-setup block**

Delete the `_path_setup` import block (approximately lines 6-29 — the entire try/except chain that imports `_path_setup`).

- [ ] **Step 5: Update TrustedHostMiddleware in main.py**

Find the `TrustedHostMiddleware` configuration and remove any `onrender.com` references. Keep `localhost`, `127.0.0.1`, `aistudyarchitect.com`, `www.aistudyarchitect.com`.

- [ ] **Step 6: Add /health/ready endpoint in main.py**

Add after the existing `/health` endpoint:

```python
@app.get("/health/ready")
def readiness_check():
    from app.core.database import test_database_connection
    from app.core.cache import redis_cache
    db_ok = test_database_connection()
    cache_ok = redis_cache.is_connected
    return {
        "status": "ready" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "cache": "connected" if cache_ok else "disconnected",
    }
```

- [ ] **Step 7: Run tests**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: All tests passing.

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/config.py backend/app/main.py
git commit -m "refactor: config for Neon + clean Render artifacts from main.py

Simplify DATABASE_URL handling (remove pg8000 path, Render rewrites).
Reduce DB_POOL_SIZE to 5 for Neon PgBouncer.
Add R2 config fields.
Remove _path_setup import chain.
Remove onrender.com from TrustedHostMiddleware.
Add /health/ready endpoint with DB + cache checks."
```

---

### Task 6: Full Cache Cleanup (atomic — redis removal + rewrite)

Remove `redis` package, `MockRedisClient`, and the traditional Redis connection path from `cache.py`. This must be atomic — all Redis references removed in one commit.

**Files:**
- Modify: `backend/app/core/cache.py` (major rewrite)
- Modify: `backend/requirements.txt` (remove redis, types-redis)
- Verify: `backend/app/core/upstash_cache.py`
- Test: `backend/tests/`

- [ ] **Step 1: Verify UpstashRedisClient implements required interface**

The `RedisCache._get_client()` returns an object that must have: `get`, `set`, `delete`, `exists`, `keys`, `ping`, `info`.

Check `upstash_cache.py` — it implements all 7 methods. Confirmed compatible.

- [ ] **Step 2: Rewrite cache.py — remove all `redis` package references**

Replace the top-level `import redis` (line 11) and `Optional[redis.Redis]` type annotation (line 25) with conditional handling:

```python
# Remove: import redis
# Change line 25 from:
#     self._redis_client: Optional[redis.Redis] = None
# To:
from typing import Any
...
    self._redis_client: Optional[Any] = None
```

In `_get_client()`, remove the traditional Redis `ConnectionPool` path entirely (lines 40-65). The method becomes:

```python
def _get_client(self):
    if self._redis_client is None:
        try:
            # Check for Upstash first (serverless Redis)
            if os.getenv("UPSTASH_REDIS_REST_URL") and os.getenv("UPSTASH_REDIS_REST_TOKEN"):
                logger.info("Using Upstash Redis via REST API")
                from app.core.upstash_cache import UpstashRedisClient
                self._redis_client = UpstashRedisClient()
                self._connected = self._redis_client.connected
                return self._redis_client

            # No cache configured — use no-op for local dev
            logger.warning("No Redis configured (set UPSTASH_REDIS_REST_URL). Caching disabled.")
            self._redis_client = _NoOpCache()
            self._connected = False
            return self._redis_client

        except Exception as e:
            logger.warning(f"Cache initialization failed: {e}")
            self._redis_client = _NoOpCache()
            self._connected = False
            return self._redis_client

    return self._redis_client
```

Delete the entire `MockRedisClient` class (lines 198-222).

Add `_NoOpCache` as a minimal fallback:

```python
class _NoOpCache:
    """Minimal no-op cache for local development without Redis."""
    def get(self, key): return None
    def set(self, key, value, ex=None): return True
    def delete(self, key): return True
    def exists(self, key): return False
    def keys(self, pattern): return []
    def ping(self): return False
    def info(self): return {}
```

- [ ] **Step 3: Remove redis and types-redis from requirements.txt**

Remove:
```
redis==5.0.1
types-redis==4.6.0.11
```

Now safe because `cache.py` no longer imports `redis` at module level.

- [ ] **Step 4: Run tests**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: All tests passing.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/cache.py backend/requirements.txt
git commit -m "refactor: remove redis package, rewrite cache for Upstash-only

Remove top-level import redis, MockRedisClient, ConnectionPool path.
Upstash is the real cache backend via REST API.
_NoOpCache is a minimal fallback for local dev without any cache.
Remove redis and types-redis from requirements.txt."
```

---

## Chunk 2: File Upload R2 Rewrite + Dockerfile + Worker + CI/CD

### Task 7: File Upload Rewrite to R2

Rewrite file upload/download/delete operations from local disk to R2.

**Files:**
- Create: `backend/app/services/storage.py` (R2 storage service)
- Modify: `backend/app/api/v1/content.py`
- Modify: `backend/app/services/content_processor.py`
- Modify: `backend/app/core/config.py` (remove UPLOAD_DIR)
- Test: `backend/tests/`

- [ ] **Step 1: Create R2 storage service**

Create `backend/app/services/storage.py`:

```python
"""R2/S3-compatible object storage service."""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Create boto3 S3 client configured for R2."""
    if not settings.R2_ENDPOINT_URL:
        logger.warning("R2 not configured (R2_ENDPOINT_URL not set)")
        return None
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )


def upload_file(key: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
    """Upload bytes to R2. Returns True on success."""
    client = _get_s3_client()
    if not client:
        return False
    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return True
    except ClientError as e:
        logger.error(f"R2 upload failed for {key}: {e}")
        return False


def download_file(key: str) -> Optional[bytes]:
    """Download bytes from R2. Returns None on failure."""
    client = _get_s3_client()
    if not client:
        return None
    try:
        response = client.get_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        return response["Body"].read()
    except ClientError as e:
        logger.error(f"R2 download failed for {key}: {e}")
        return None


def delete_file(key: str) -> bool:
    """Delete object from R2. Returns True on success."""
    client = _get_s3_client()
    if not client:
        return False
    try:
        client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        logger.error(f"R2 delete failed for {key}: {e}")
        return False


def generate_presigned_url(key: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a presigned download URL. Returns None on failure."""
    client = _get_s3_client()
    if not client:
        return None
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
    except ClientError as e:
        logger.error(f"R2 presigned URL failed for {key}: {e}")
        return None
```

- [ ] **Step 2: Update content.py — rewrite save_upload_file()**

Replace local disk writes with R2 uploads. Replace `FileResponse` downloads with presigned URL redirects. Replace `Path.unlink()` deletes with R2 `delete_object`. Remove `UPLOAD_DIR` constant and module-level `mkdir()`.

This is a large file — the specific functions to modify are `save_upload_file()`, `download_content`, `delete_content`, and `bulk_delete_content`. Import from the new storage service:

```python
from app.services.storage import upload_file, download_file, delete_file, generate_presigned_url
```

For download, use:
```python
from fastapi.responses import RedirectResponse

url = generate_presigned_url(content.file_path)
if url:
    return RedirectResponse(url=url)
```

- [ ] **Step 3: Update content_processor.py — download from R2 to temp dir**

In `process_file()`, instead of reading from local disk path, download from R2 to a temp file:

```python
import tempfile
from app.services.storage import download_file

# Download from R2 to temp file
data = download_file(file_path)
if data is None:
    raise FileNotFoundError(f"Could not download {file_path} from R2")

with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_path).suffix) as tmp:
    tmp.write(data)
    local_path = tmp.name

try:
    # Process using local_path (existing processing logic)
    ...
finally:
    # Clean up temp file
    Path(local_path).unlink(missing_ok=True)
```

Remove dead `self.upload_dir` from `__init__`.

- [ ] **Step 4: Remove UPLOAD_DIR from config.py**

Remove line 83:
```python
    UPLOAD_DIR: str = "uploads"
```

- [ ] **Step 5: Run tests**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: Tests pass. Some content upload tests may need mocking for R2 — update them to mock `app.services.storage` functions.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/storage.py backend/app/api/v1/content.py backend/app/services/content_processor.py backend/app/core/config.py
git commit -m "feat: rewrite file operations from local disk to R2

New storage service wraps boto3 for R2.
Upload: put_object, Download: presigned URL redirect,
Delete: delete_object, Process: temp file pattern.
Remove UPLOAD_DIR config and local disk references."
```

---

### Task 8: Dockerfile + Render Cleanup

Write clean Dockerfile, remove Render artifacts.

**Files:**
- Create: `backend/Dockerfile`
- Remove: `backend/Dockerfile.render`
- Remove: `backend/render.yaml`
- Remove: `backend/render-crons.yaml`
- Remove: `backend/build.sh`
- Remove: `backend/start_render.sh`
- Remove: `backend/app/_path_setup.py`

- [ ] **Step 1: Create backend/Dockerfile**

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

- [ ] **Step 2: Test Docker build locally**

```bash
cd backend
docker build -t study-architect-backend .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="sqlite:///./test.db" \
  -e JWT_SECRET_KEY="test-secret" \
  -e SECRET_KEY="test-secret" \
  study-architect-backend
```

Expected: Container starts, uvicorn logs show server running on port 8000. Ctrl+C to stop.

- [ ] **Step 3: Remove Render artifacts**

```bash
cd backend
rm -f Dockerfile.render render.yaml render-crons.yaml build.sh start_render.sh
rm -f app/_path_setup.py
```

- [ ] **Step 4: Commit**

```bash
git add backend/Dockerfile
git rm backend/Dockerfile.render backend/render.yaml backend/render-crons.yaml backend/build.sh backend/start_render.sh backend/app/_path_setup.py 2>/dev/null
git commit -m "feat: clean Dockerfile + remove all Render artifacts

New Dockerfile: python:3.12-slim, libmagic1, uvicorn CMD.
Removed: Dockerfile.render, render.yaml, render-crons.yaml,
build.sh, start_render.sh, _path_setup.py."
```

---

### Task 9: CF Worker + wrangler.toml

Create the CF Worker entry point and wrangler configuration.

**Files:**
- Create: `worker/index.ts`
- Create: `worker/package.json`
- Create: `wrangler.toml`

- [ ] **Step 0: Research current CF Containers wrangler.toml schema**

Consult `@cloudflare` and `@wrangler` skills to verify the exact syntax for CF Containers. The `[containers]` section and `env.CONTAINER` binding pattern below are based on current docs but may need adjustment.

- [ ] **Step 1: Create worker/wrangler.toml (same dir as package.json)**

```toml
name = "study-architect"
compatibility_date = "2024-01-01"

[containers]
  image = "./backend"
  instance_type = "basic"
  max_instances = 1

[[containers.ports]]
  port = 8000
  protocol = "http"
```

Note: The exact wrangler.toml format for Containers may need adjustment based on current CF Containers docs. Consult `@cloudflare` and `@wrangler` skills during implementation to get the correct syntax.

- [ ] **Step 2: Create worker/package.json**

```json
{
  "name": "study-architect-worker",
  "private": true,
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "deploy:staging": "wrangler deploy --env staging"
  },
  "devDependencies": {
    "wrangler": "^4"
  }
}
```

- [ ] **Step 3: Create worker/index.ts**

```typescript
export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const url = new URL(request.url);

    // Block API documentation endpoints
    const blocked = ["/api/docs", "/api/openapi.json", "/api/redoc"];
    if (blocked.some((path) => url.pathname === path)) {
      return new Response("Not Found", { status: 404 });
    }

    // Handle CORS preflight — mirror backend's allowed origins, not wildcard
    // (wildcard + credentials is prohibited by CORS spec)
    if (request.method === "OPTIONS") {
      const origin = request.headers.get("Origin") || "";
      const allowed = [
        "https://aistudyarchitect.com",
        "https://www.aistudyarchitect.com",
      ];
      const allowOrigin = allowed.includes(origin) ? origin : "";
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": allowOrigin,
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization, X-CSRF-Token",
          "Access-Control-Allow-Credentials": "true",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    // Route /api/* to the container
    if (url.pathname.startsWith("/api/")) {
      const container = env.CONTAINER;
      return container.fetch(request);
    }

    // Everything else returns 404 (frontend is on Vercel)
    return new Response("Not Found", { status: 404 });
  },
};
```

Note: The `env.CONTAINER` binding pattern is specific to CF Containers. Verify exact syntax with `@cloudflare` and `@wrangler` skills during implementation.

- [ ] **Step 4: Install wrangler and test locally**

```bash
cd worker
npm install
npx wrangler dev
```

Expected: Worker starts locally. Test: `curl http://localhost:8787/api/v1/health` proxies to container.

- [ ] **Step 5: Commit**

```bash
git add worker/
git commit -m "feat: CF Worker + wrangler.toml for Container routing

Worker routes /api/* to Container, blocks /api/docs,
handles CORS preflight at edge."
```

---

### Task 10: CI/CD Pipelines

Write `deploy.yml`, rewrite `staging.yml` and `backup.yml`.

**Files:**
- Create: `.github/workflows/deploy.yml`
- Modify: `.github/workflows/staging.yml`
- Modify: `.github/workflows/backup.yml`

- [ ] **Step 1: Create .github/workflows/deploy.yml**

```yaml
name: Deploy to Cloudflare

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run backend tests
        run: |
          cd backend
          pytest tests/ -v --tb=short
        env:
          JWT_SECRET_KEY: test-secret
          SECRET_KEY: test-secret
          DATABASE_URL: postgresql+psycopg2://test:test@localhost:5432/test_db

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "18"

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Run frontend tests
        run: |
          cd frontend
          npm test -- --run

  migrate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install migration dependencies
        run: |
          cd backend
          pip install alembic sqlalchemy psycopg2-binary pydantic pydantic-settings python-dotenv

      - name: Run Alembic migrations
        run: |
          cd backend
          alembic upgrade head
        env:
          DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}

  deploy:
    needs: migrate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "18"

      - name: Install wrangler
        run: |
          cd worker
          npm ci

      - name: Deploy to Cloudflare
        run: |
          cd worker
          npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}

      - name: Health check
        run: |
          sleep 10
          response=$(curl -s -o /dev/null -w "%{http_code}" https://aistudyarchitect.com/api/v1/health/ready)
          if [ "$response" != "200" ]; then
            echo "Health check failed with status $response"
            exit 1
          fi
          echo "Health check passed"
```

- [ ] **Step 2: Rewrite .github/workflows/backup.yml**

```yaml
name: Database Backups

on:
  schedule:
    - cron: '0 2 * * *'     # Daily at 2 AM UTC
    - cron: '0 3 * * 0'     # Weekly Sundays at 3 AM UTC
  workflow_dispatch:
    inputs:
      provider:
        description: 'Backup destination (r2, s3, or both)'
        required: false
        default: 'both'
        type: choice
        options: [r2, s3, both]

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Install PostgreSQL client
        run: |
          sudo sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
          curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
          sudo apt-get update
          sudo apt-get install -y postgresql-client-17

      - name: Determine provider
        id: provider
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "provider=${{ github.event.inputs.provider }}" >> $GITHUB_OUTPUT
          elif [ "$(date +%u)" = "7" ]; then
            echo "provider=both" >> $GITHUB_OUTPUT
          else
            echo "provider=r2" >> $GITHUB_OUTPUT
          fi

      - name: Dump database
        run: |
          DATE=$(date +%Y-%m-%d)
          pg_dump "${{ secrets.NEON_DATABASE_URL }}" | gzip > backup-${DATE}.sql.gz
          echo "BACKUP_FILE=backup-${DATE}.sql.gz" >> $GITHUB_ENV
          echo "BACKUP_DATE=${DATE}" >> $GITHUB_ENV

      - name: Upload to R2
        if: steps.provider.outputs.provider == 'r2' || steps.provider.outputs.provider == 'both'
        env:
          R2_ENDPOINT_URL: ${{ secrets.R2_ENDPOINT_URL }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
        run: |
          pip install boto3
          python -c "
          import boto3, os
          s3 = boto3.client('s3',
              endpoint_url=os.environ['R2_ENDPOINT_URL'],
              aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
              aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'])
          s3.upload_file(
              os.environ['BACKUP_FILE'],
              'study-architect-storage',
              f'backups/{os.environ[\"BACKUP_DATE\"]}/{os.environ[\"BACKUP_FILE\"]}')
          print('R2 upload complete')
          "

      - name: Upload to S3
        if: steps.provider.outputs.provider == 's3' || steps.provider.outputs.provider == 'both'
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          pip install boto3
          python -c "
          import boto3, os
          s3 = boto3.client('s3',
              aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
              aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
          s3.upload_file(
              os.environ['BACKUP_FILE'],
              'ai-study-architect-backup-2025',
              f'backups/production/aws_s3/{os.environ[\"BACKUP_FILE\"]}')
          print('S3 upload complete')
          "
```

- [ ] **Step 3: Rewrite .github/workflows/staging.yml**

Replace the Render API deploy steps with:
```yaml
      - name: Deploy to staging
        if: github.event_name == 'push'
        run: |
          cd worker
          npm ci
          npx wrangler deploy --env staging
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

Keep the test jobs unchanged.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy.yml .github/workflows/backup.yml .github/workflows/staging.yml
git commit -m "feat: CI/CD pipelines for Cloudflare

New deploy.yml: test -> migrate -> deploy -> health check.
Rewrite backup.yml: pg_dump Neon -> R2/S3.
Rewrite staging.yml: wrangler deploy --env staging."
```

---

### Task 11: Documentation Cleanup

Update CLAUDE.md, remove Render references, update project memory.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `DEPLOYMENT.md`

- [ ] **Step 1: Update CLAUDE.md**

Replace Render references throughout:
- Platform-Specific Considerations: remove "Render Platform Constraints" section
- Deployment references: update to CF Containers
- Environment variables: update for Neon/R2/Upstash
- Troubleshooting table: remove Render-specific entries

- [ ] **Step 2: Update DEPLOYMENT.md**

Rewrite for CF Container deployment flow instead of Render.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md DEPLOYMENT.md
git commit -m "docs: update for Cloudflare infrastructure

Remove all Render references. Document CF Containers + Neon +
R2 + Upstash deployment flow."
```

---

### Task 12: Deploy + Verify

Deploy to Cloudflare and verify end-to-end.

**Files:** None (deployment + verification)

- [ ] **Step 1: Set GitHub secrets**

Go to GitHub repo Settings > Secrets > Actions. Add:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `NEON_DATABASE_URL`
- `R2_ENDPOINT_URL`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `UPSTASH_REDIS_REST_URL`
- `UPSTASH_REDIS_REST_TOKEN`

Remove old secrets:
- `RENDER_API_KEY`
- `STAGING_SERVICE_ID`
- `BACKUP_TOKEN`

- [ ] **Step 2: Set container environment variables**

In wrangler.toml or CF dashboard, set all env vars from the spec's Configuration & Security table (DATABASE_URL, JWT_SECRET_KEY, ANTHROPIC_API_KEY, etc.).

- [ ] **Step 3: Deploy**

```bash
cd worker
npx wrangler deploy
```

- [ ] **Step 4: Verify health**

```bash
curl https://aistudyarchitect.com/api/v1/health
curl https://aistudyarchitect.com/api/v1/health/ready
```

Expected: `/health` returns `{"status": "healthy"}`. `/health/ready` returns `{"status": "ready", "database": "connected", "cache": "connected"}`.

- [ ] **Step 5: Verify blocked endpoints**

```bash
curl -s -o /dev/null -w "%{http_code}" https://aistudyarchitect.com/api/docs
curl -s -o /dev/null -w "%{http_code}" https://aistudyarchitect.com/api/openapi.json
```

Expected: both return `404`.

- [ ] **Step 6: Verify auth flow**

```bash
# Register a test user
curl -X POST https://aistudyarchitect.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!", "username": "testuser"}'

# Login
curl -X POST https://aistudyarchitect.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!"}'
```

Expected: Registration returns user object. Login returns JWT token.

- [ ] **Step 7: Verify frontend connects**

Open https://aistudyarchitect.com in browser. Login form should render (Vercel). Submit login — should hit the CF Container backend and authenticate.

- [ ] **Step 8: Final commit + push**

```bash
git push origin main
```

This triggers the deploy.yml workflow. Verify it passes in GitHub Actions.
