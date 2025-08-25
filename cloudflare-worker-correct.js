export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Route /api/* to backend WITHOUT stripping /api
    // Backend expects /api/v1/... paths
    if (url.pathname.startsWith('/api/')) {
      const backendUrl = new URL(url);
      backendUrl.hostname = 'ai-study-architect.onrender.com';
      // Keep the full path including /api
      
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