# Vercel Environment Variable Update Required

## IMPORTANT: Manual Action Needed

To complete the proxy setup, you need to update the environment variable in Vercel:

### Steps:
1. Go to https://vercel.com/dashboard
2. Select your project: `ai-study-architect` 
3. Go to Settings → Environment Variables
4. Find `VITE_API_URL`
5. Change the value from: `https://ai-study-architect.onrender.com`
6. To: `` (empty string)
7. Click Save
8. Vercel will automatically redeploy

### Why this is needed:
- The proxy in vercel.json routes `/api/*` to the backend
- Frontend should use relative paths (no domain)
- Empty VITE_API_URL means axios will use relative paths
- Cookies will work as same-origin

### After deployment:
The authentication flow will work properly with httpOnly cookies because:
- Frontend: www.aistudyarchitect.com
- API calls: www.aistudyarchitect.com/api/* (proxied to backend)
- Cookies: Set for www.aistudyarchitect.com (same-origin)

### Testing:
Once deployed, test:
1. Login (with and without remember me)
2. Refresh page (should stay logged in)
3. Close tab and reopen (should stay logged in)
4. Logout (should clear cookies)