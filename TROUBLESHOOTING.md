# Troubleshooting Guide

## Chat/AI Response Issues

### Problem: Empty or Blank AI Responses (Fixed 2025-08-23)

**Symptoms:**
- Chat interface shows user messages but AI responses are empty
- Network tab shows 200 OK but response has 0 completion tokens
- SSE stream starts but contains no content

**Root Causes:**
1. **API keys loading at import time** - Services were checking for API keys before environment variables were loaded
2. **Async client lifecycle issue** - Streaming client was closing before generator could use it

**Solution:**
```python
# backend/app/services/claude_service.py
# 1. Use @property decorator for runtime API key evaluation
@property
def api_key(self):
    """Get API key at runtime, not import time"""
    return os.getenv("ANTHROPIC_API_KEY")

# 2. Create wrapper method to manage client lifecycle for streaming
async def _stream_claude_response_wrapper(self, payload: Dict[str, Any]) -> AsyncIterator[str]:
    """Wrapper that manages its own client for streaming"""
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        async for chunk in self._stream_claude_response(client, payload):
            yield chunk
```

**Testing:**
```bash
# Test with curl
curl -X POST "https://ai-study-architect.onrender.com/api/v1/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"messages":[{"role":"user","content":"Test message"}],"stream":true}' \
  --no-buffer
```

---

## Authentication Issues

### Problem: CSRF Token Mismatch

**Symptoms:**
- 403 Forbidden errors on API calls
- "CSRF token mismatch" in response

**Root Cause:**
- JWT-protected endpoints don't need CSRF protection (double protection)

**Solution:**
Added exemptions in `backend/app/core/csrf.py`:
```python
# Exempt JWT-protected endpoints
if path == "/api/v1/" or path.startswith("/api/v1/agents/"):
    return True
```

### Problem: Authorization Header Missing

**Symptoms:**
- 401 Unauthorized despite being logged in
- Authorization header not sent in requests

**Root Cause:**
- Using `credentials: 'include'` causes browser to strip Authorization header

**Solution:**
Use `credentials: 'omit'` for JWT-protected endpoints:
```typescript
// frontend/src/components/chat/ChatInterface.tsx
const fetchResponse = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(chatRequest),
    credentials: 'omit'  // Preserve Authorization header
})
```

---

## Database Issues

### Problem: Alembic "relation already exists" Error

**Symptoms:**
- Deployment fails with "relation users already exists"
- Migration errors during deployment

**Solution:**
- Leave Pre-Deploy Command **EMPTY** in Render dashboard
- Migrations are handled in `start_render.sh` with proper error handling

### Problem: Windows PostgreSQL Port Issue

**Symptoms:**
- Cannot connect to database on Windows
- Connection refused on port 5432

**Solution:**
- Windows PostgreSQL uses port 5433 (not standard 5432)
- Update connection string accordingly

---

## Deployment Issues

### Problem: Frontend 404 on Direct Route Access

**Symptoms:**
- Refreshing page on `/study` returns 404
- Direct navigation to routes fails

**Solution:**
- Configured in `vercel.json` for SPA routing:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

### Problem: Build Fails on System Packages

**Symptoms:**
- "apt-get: command not found" errors
- Cannot install system dependencies

**Root Cause:**
- Render Starter plan has no root access

**Solution:**
- Use Python packages instead of system packages
- PostgreSQL backup uses psycopg2 instead of pg_dump

---

## Environment Variable Issues

### Problem: API Keys Not Detected Despite Being Set

**Symptoms:**
- Logs show "No API key found" but keys are set in Render
- Services report missing configuration

**Root Cause:**
- Services checking API keys at module import time

**Solution:**
- Use runtime evaluation with @property decorators
- Check environment variables when needed, not at import

---

## Redis/Cache Issues

### Problem: Redis Connection Fails

**Symptoms:**
- "Connection refused" errors for Redis
- Cache operations failing

**Solution:**
- System automatically falls back to MockRedisClient
- No external Redis needed - in-memory cache works fine

---

## Common Frontend-Backend Mismatch

### Problem: Confusion About Where Frontend is Hosted

**Important Reminder:**
- **Frontend**: Hosted on **Vercel** (https://ai-study-architect.vercel.app)
- **Backend**: Hosted on **Render** (https://ai-study-architect.onrender.com)
- **NOT** both on Render

---

## Backup System Issues

### Problem: Rate Limit on Manual Backups

**Symptoms:**
- "Backup already run recently" error

**Solution:**
- Wait 1 hour between manual backup triggers
- Automatic backups run on schedule (R2 daily, S3 weekly)

### Problem: Cannot Decrypt Backup

**Symptoms:**
- Decryption fails with invalid key error

**Critical:**
- **NEVER** change `BACKUP_ENCRYPTION_KEY`
- Key is stored in Proton Pass - do not lose it
- All backups use the same encryption key

---

## Quick Diagnostic Commands

### Check Service Health
```bash
# Production
curl https://ai-study-architect.onrender.com/api/v1/health

# Check AI service status (requires auth)
curl https://ai-study-architect.onrender.com/api/v1/debug/ai-status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Chat Functionality
```bash
# Get token first
TOKEN=$(curl -X POST https://ai-study-architect.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_USER&password=YOUR_PASS&grant_type=password" \
  | jq -r '.access_token')

# Test chat
curl -X POST "https://ai-study-architect.onrender.com/api/v1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Test"}],"stream":false}'
```

### Check Logs (with Render MCP)
If you have Render MCP configured in Claude Code:
- "Show me recent error logs for ai-study-architect"
- "What's the memory usage of my service?"
- "List recent deploys and their status"

---

## Prevention Tips

1. **Always test locally first** before deploying
2. **Check Render logs** immediately after deployment
3. **Use the debug endpoint** (`/api/v1/debug/ai-status`) to verify AI services
4. **Monitor with Render MCP** for real-time insights
5. **Keep Pre-Deploy empty** in Render settings
6. **Verify environment variables** are set in Render dashboard

---

## Emergency Recovery

If everything is broken:
1. Check Render service logs first
2. Verify environment variables in Render dashboard
3. Test with curl commands (not browser) to isolate issues
4. Check GitHub Actions for deployment status
5. Use Render MCP to query service status
6. Rollback to previous deployment if needed (Render dashboard)

---

## Contact for Help

- GitHub Issues: https://github.com/belumume/ai-study-architect/issues
- Check DOCUMENTATION_INDEX.md for specific guides
- Review CLAUDE.md for development commands