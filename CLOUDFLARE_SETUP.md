# Cloudflare Configuration for True Same-Origin

This setup gives us the best of everything:
- True same-origin (no CORS needed)
- No proxy overhead
- Direct streaming
- Better security
- Optimal performance

## Option 1: Using Cloudflare Workers (Recommended)

### Step 1: Create the Worker

1. Go to Cloudflare Dashboard → Workers & Pages
2. Create a new Worker
3. Name it: `ai-study-architect-router`
4. Copy the content from `cloudflare-worker.js`
5. Save and Deploy

### Step 2: Configure Routes

1. Go to your Worker → Settings → Triggers
2. Add Custom Domain: `aistudyarchitect.com`
3. Add Custom Domain: `www.aistudyarchitect.com`

### Step 3: Update DNS

1. Remove/disable any existing A/CNAME records for `aistudyarchitect.com` and `www`
2. The Worker will handle all routing

## Option 2: Using Cloudflare Origin Rules (Simpler but Less Flexible)

### Step 1: Set Default Origin

1. Go to Cloudflare Dashboard → DNS
2. Set CNAME for `@` and `www` to `ai-study-architect.vercel.app`
3. Enable Proxy (orange cloud)

### Step 2: Create Origin Rule

1. Go to Rules → Origin Rules
2. Create new rule:
   - Name: "Route API to Render"
   - When: `URI Path starts with /api/`
   - Then: Override destination to `ai-study-architect.onrender.com`
   - Deploy

## Option 3: Keep Subdomain (Simplest but Not Same-Origin)

If you prefer to keep it simple with `api.aistudyarchitect.com`:

1. The custom domain is already configured in Render
2. Backend code has been updated to accept the host
3. Just update frontend to call `https://api.aistudyarchitect.com` directly

## Frontend Configuration

After choosing your option, update the frontend API base URL:

### For Options 1 & 2 (Same-Origin):
```javascript
// .env.production
VITE_API_URL=  // Leave empty for same-origin
```

### For Option 3 (Subdomain):
```javascript
// .env.production
VITE_API_URL=https://api.aistudyarchitect.com
```

## Benefits of Each Option

| Aspect | Option 1 (Worker) | Option 2 (Origin Rules) | Option 3 (Subdomain) |
|--------|------------------|------------------------|---------------------|
| Same-Origin | ✅ Yes | ✅ Yes | ❌ No (CORS needed) |
| Setup Complexity | Medium | Easy | Easiest |
| Flexibility | High | Medium | Low |
| Performance | Best | Best | Good |
| Maintenance | Low | Lowest | Low |
| Cost | Free (100k req/day) | Free | Free |

## Recommendation

**Use Option 1 (Cloudflare Worker)** for the best performance and true same-origin without any compromises. It's the most flexible and gives us everything we want.