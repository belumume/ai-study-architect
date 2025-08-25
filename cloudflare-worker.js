export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Route /api/* to backend WITHOUT stripping /api
    if (url.pathname.startsWith('/api/')) {
      const backendUrl = new URL(url);
      backendUrl.hostname = 'ai-study-architect.onrender.com';
      
      // SECURITY: Block OpenAPI/docs exposure
      if (url.pathname === '/api/docs' || 
          url.pathname === '/api/openapi.json' ||
          url.pathname === '/api/redoc') {
        return new Response('Not Found', { status: 404 });
      }
      
      // Keep the full path - backend expects /api/v1/*
      // DO NOT strip /api prefix
      
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