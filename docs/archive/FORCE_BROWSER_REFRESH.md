# EMERGENCY BROWSER CACHE FIX - NUCLEAR OPTION

---
Document Level: 4
Created: August 2025
Last Updated: August 2025
Supersedes: None
Status: Archived
---

## THE PROBLEM
Your browser is serving OLD JavaScript files from its HTTP cache. The code HAS been updated but the browser refuses to load the new version.

## THE NUCLEAR SOLUTION

### Step 1: KILL EVERYTHING
```bash
# Close ALL browser windows and terminals
# Then run:
taskkill /F /IM chrome.exe 2>nul
taskkill /F /IM firefox.exe 2>nul
taskkill /F /IM msedge.exe 2>nul
taskkill /F /IM node.exe 2>nul
```

### Step 2: CLEAR VITE CACHE COMPLETELY
```bash
cd /mnt/c/Users/elzai/DEV/cs50/project/frontend
rm -rf node_modules/.vite
rm -rf node_modules/.cache
rm -rf dist
rm -rf .parcel-cache
```

### Step 3: START VITE WITH CACHE BUSTING
```bash
# This forces Vite to add cache-busting timestamps to ALL files
cd frontend
npm run dev -- --force --clearScreen false --host
```

### Step 4: BROWSER HARD REFRESH SEQUENCE
1. Open NEW browser window
2. Open DevTools FIRST (F12)
3. Go to Network tab
4. Check "Disable cache" checkbox
5. Navigate to http://localhost:5173
6. Hold Ctrl+Shift and click Reload button multiple times

### Step 5: VERIFY IT'S WORKING
In browser DevTools Network tab, you should see:
- Requests going to `/api/v1/chat/` (NOT full URL)
- Status 200 or 401 (NOT 404)
- Request URL starts with `http://localhost:8000` (proxied)

## IF STILL BROKEN - ULTIMATE NUCLEAR OPTION

### Option A: Use Different Port
```bash
cd frontend
npm run dev -- --port 5174 --force
```
Then go to http://localhost:5174

### Option B: Use Incognito Mode
1. Close all incognito windows
2. Open fresh incognito window (Ctrl+Shift+N)
3. Navigate to http://localhost:5173
4. Open DevTools and check Network tab

### Option C: Use Different Browser
Try Firefox or Edge if using Chrome

## THE REAL FIX - PREVENT FUTURE ISSUES

Add this to your `vite.config.ts`:
```typescript
server: {
  watch: {
    usePolling: true,
  },
  hmr: {
    overlay: true,
  },
  // Force cache busting in development
  headers: {
    'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0',
  }
}
```

## WHAT'S HAPPENING?
- Browser cached the OLD JavaScript files with hardcoded URLs
- Normal refresh doesn't reload JavaScript modules 
- Vite HMR (Hot Module Replacement) isn't triggering for some reason
- The nuclear option forces EVERYTHING to reload fresh

## SUCCESS INDICATORS
✅ Browser console shows `/api/v1/chat/` (relative URL)
✅ Network tab shows requests proxied to port 8000
✅ Backend logs show incoming requests
✅ AI chat responds with actual file content