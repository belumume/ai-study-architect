export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Route /api/* to backend with smart path handling
    if (url.pathname.startsWith('/api/')) {
      const backendUrl = new URL(url);
      backendUrl.hostname = 'ai-study-architect.onrender.com';
      
      // Smart routing:
      // - /api/health → /health (strip /api for root endpoints)
      // - /api/v1/* → /api/v1/* (keep as is for versioned API)
      if (url.pathname === '/api/health') {
        backendUrl.pathname = '/health';
      }
      // For all other /api/* paths, keep them as is
      // This includes /api/v1/auth/*, /api/v1/content/*, etc.
      
      const modifiedHeaders = new Headers(request.headers);
      modifiedHeaders.set('X-Forwarded-Host', url.hostname);
      modifiedHeaders.set('X-Forwarded-Proto', url.protocol.replace(':', ''));
      
      return fetch(new Request(backendUrl, {
        method: request.method,
        headers: modifiedHeaders,
        body: request.body,
        redirect: 'follow'
      }));
    }
    
    // Route everything else to frontend (Vercel)
    const frontendUrl = new URL(url);
    frontendUrl.hostname = 'ai-study-architect.vercel.app';
    
    return fetch(new Request(frontendUrl, request));
  }
};