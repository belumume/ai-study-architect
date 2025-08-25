# Critical Session Summary - All August 2025 Sessions

## From Previous Compacted Sessions

### JWT Security Implementation (Aug 24)
- Implemented RS256 (asymmetric) JWT tokens with automatic key generation
- Keys stored in `backend/keys/` directory (gitignored)
- Automatic fallback to HS256 if RS256 fails
- Token verification handles both algorithms for backward compatibility
- Access tokens: 30 min, Refresh tokens: 7 days (30 days with remember_me)

### CSRF Protection Architecture (Aug 24)
- Double-submit cookie pattern implementation
- Strategic exemptions for JWT-authenticated endpoints
- CSRF token generation uses signed timestamps
- Exempted paths: /health, /csrf/token, /auth/login, /auth/register, /admin/public-key
- All JWT-authenticated endpoints exempted (they use Authorization header)

### Cloudflare Worker Evolution (Aug 24-25)
**Initial attempts (WRONG):**
- Tried stripping /api prefix - FAILED
- Backend expects full /api/v1/* paths

**Final working configuration:**
- Routes /api/* to backend WITHOUT modifying path
- Routes everything else to Vercel frontend
- Blocks API documentation endpoints (/api/docs, /api/openapi.json, /api/redoc)
- Enables true same-origin architecture

### Database Migration Issues Solved
- NEVER use Pre-Deploy command in Render
- Database has existing tables from before Alembic
- Migrations handled in start_render.sh with proper error handling
- "Table already exists" errors are expected and handled

### Authentication Flow Fixed (Aug 24)
1. Login returns access_token, refresh_token, and sets CSRF cookie
2. Frontend stores tokens in localStorage (tokenStorage.ts)
3. API requests include both Authorization header and X-CSRF-Token
4. httpOnly CSRF cookie provides XSS protection
5. Remember Me extends refresh token to 30 days

### Redis/Caching Architecture
- No external Redis required
- MockRedisClient provides in-memory fallback
- Automatically switches between Redis and mock based on availability
- Agent state management works with both

### Security Vulnerabilities Found & Fixed (Aug 25)
**4 endpoints were exposed without auth:**
1. `/api/v1/tutor/progress`
2. `/api/v1/content/stats`
3. `/api/v1/agents/status`
4. `/api/v1/chat/history`

All now properly return 401/403 without authentication.

## Configuration Truths

### What MUST Stay Constant
1. **BACKUP_ENCRYPTION_KEY** - Changing loses all backup access
2. **Pre-Deploy Command** - Must be EMPTY in Render
3. **Worker Path Handling** - Must NOT strip /api prefix
4. **PostgreSQL Port** - 5433 on Windows (not 5432)
5. **7 Agents** - Not 5, not 6, always 7

### Environment-Specific Settings
**Development:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- CORS required between ports

**Production:**
- Single domain: https://aistudyarchitect.com
- Worker routes /api/* to Render backend
- No CORS needed (same-origin)
- API docs blocked at edge

### File Organization
**Critical configs:**
- `cloudflare-worker.js` - Edge routing (DO NOT modify path stripping)
- `backend/app/core/csrf.py` - CSRF with JWT exemptions
- `backend/app/core/security.py` - JWT with RS256/HS256 fallback
- `backend/start_render.sh` - Handles migrations safely
- `frontend/src/services/api.ts` - Axios with auth/CSRF interceptors

### Testing Completed
- All 48 API endpoints tested through production domain
- 6 public endpoints working correctly
- 42 protected endpoints properly secured
- 0 data leaks or exposures
- API documentation successfully hidden

## Deployment Architecture

### Current Setup
```
User -> Cloudflare Worker (aistudyarchitect.com)
         ├─> /api/* -> Render Backend (ai-study-architect.onrender.com)
         └─> /* -> Vercel Frontend (ai-study-architect.vercel.app)
```

### Why This Architecture
1. **True same-origin** - No CORS complexity
2. **Edge performance** - Cloudflare's global network
3. **Security** - API structure hidden, docs blocked
4. **Simplicity** - Single domain for users
5. **Scalability** - Each service scales independently

## Lessons Learned

### What Didn't Work
- Stripping /api prefix in Worker (backend expects full paths)
- Using Pre-Deploy for migrations (conflicts with existing tables)
- Subdomain approach (api.aistudyarchitect.com) - CORS complexity
- Port 3000 references (frontend uses 5173)

### What Works Perfectly
- RS256 JWT with HS256 fallback
- CSRF double-submit with JWT exemptions
- MockRedisClient fallback pattern
- Cloudflare Worker for same-origin
- Security at every layer

## For Future Sessions

### Always Check
1. Git status before making changes
2. All 48 endpoints remain secure
3. Worker still blocks API docs
4. JWT keys exist in backend/keys/
5. CSRF exemptions still configured

### Never Forget
- Backend expects /api/v1/* (full paths)
- Pre-Deploy must be empty
- 7 agents, not 5 or 6
- Port 5433 for PostgreSQL on Windows
- Frontend is on Vercel, not Render

---
*Compiled from all August 2025 sessions including the compacted session context*
*Last updated: August 25, 2025*