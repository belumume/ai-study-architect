# Frontend Deployment - Vercel

## Quick Deploy (2 methods)

### Method 1: Via GitHub (Recommended)
1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Sign up/login with GitHub
4. Click "Add New..." → "Project"
5. Import your repository
6. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `project/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
7. Add Environment Variable:
   - `VITE_API_URL` = `https://ai-study-architect.onrender.com`
8. Click "Deploy"

### Method 2: Via CLI
```bash
# Install Vercel CLI
npm i -g vercel

# In frontend directory
cd frontend

# Deploy
vercel

# Follow prompts:
# - Setup and deploy: Y
# - Which scope: (your account)
# - Link to existing project: N
# - Project name: ai-study-architect
# - Directory: ./
# - Override settings: N

# For production deployment
vercel --prod
```

## Your URLs
- **Development**: `https://ai-study-architect-xxx.vercel.app`
- **Production**: `https://ai-study-architect.vercel.app`

## Environment Variables
Set in Vercel dashboard → Settings → Environment Variables:
```
VITE_API_URL=https://ai-study-architect.onrender.com
```

## Auto-Deploy Setup
1. In Vercel dashboard → Settings → Git
2. Production Branch: `main`
3. Auto-deploy: Enabled

Now every push to `main` auto-deploys!

## Testing Locally with Production API
```bash
# Use production API locally
VITE_API_URL=https://ai-study-architect.onrender.com npm run dev
```

## Troubleshooting

### CORS Errors
- Ensure backend has `BACKEND_CORS_ORIGINS=*` or your Vercel URL
- Check Network tab for actual error

### API Not Connecting
- Verify `VITE_API_URL` is set in Vercel
- Check if Render backend is running
- Test API directly: `https://ai-study-architect.onrender.com/api/v1/health`

### Build Failing
- Check build logs in Vercel dashboard
- Run `npm run build` locally first
- Ensure all TypeScript errors are fixed

## Custom Domain (Optional)
1. Buy domain (e.g., studyarchitect.ai)
2. In Vercel: Settings → Domains
3. Add domain and follow DNS instructions

## Performance Tips
- Vercel auto-optimizes React builds
- Images served from Vercel's CDN
- API calls cached at edge when possible