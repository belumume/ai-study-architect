# Deployment Notes

## IMPORTANT: Add to Render Environment Variables

**SECURITY: DO NOT include localhost in production!**

Add this environment variable in Render dashboard:

```
BACKEND_CORS_ORIGINS=https://www.aistudyarchitect.com,https://aistudyarchitect.com,https://ai-study-architect.vercel.app
```

This allows ONLY the production frontend domains to communicate with the backend API.

**Note**: localhost origins are automatically excluded from production for security.
Only include localhost in your local `.env` file for development.

## Frontend Domains
- Production: https://www.aistudyarchitect.com (custom domain)
- Production Alt: https://aistudyarchitect.com (without www)
- Vercel Default: https://ai-study-architect.vercel.app
- Local Dev: http://localhost:5173 (Vite)
- Local Dev Alt: http://localhost:3000 (React default)

## Backend API
- Production: https://ai-study-architect.onrender.com
- Local Dev: http://localhost:8000

## Recent Fixes (Aug 23, 2025)
1. Fixed chat endpoint path - was `/api/v1/chat/`, should be `/api/v1/`
2. Fixed frontend to use VITE_API_URL for all API calls
3. Added production domains to CORS configuration