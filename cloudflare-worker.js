// Cloudflare Worker for AI Study Architect
// Routes /api/* to Render backend, everything else to Vercel frontend

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Route API requests to Render backend
    if (url.pathname.startsWith('/api/')) {
      // Modify the request to go to Render
      const backendUrl = new URL(url);
      backendUrl.hostname = 'ai-study-architect.onrender.com';
      
      // Clone the request with the new URL
      const backendRequest = new Request(backendUrl, request);
      
      // Add proper headers
      const modifiedHeaders = new Headers(backendRequest.headers);
      modifiedHeaders.set('X-Forwarded-Host', url.hostname);
      modifiedHeaders.set('X-Forwarded-Proto', url.protocol.replace(':', ''));
      
      // Forward to backend
      return fetch(new Request(backendUrl, {
        method: request.method,
        headers: modifiedHeaders,
        body: request.body,
        redirect: 'follow'
      }));
    }
    
    // Route everything else to Vercel frontend
    const frontendUrl = new URL(url);
    frontendUrl.hostname = 'ai-study-architect.vercel.app';
    
    // Forward to frontend
    return fetch(new Request(frontendUrl, request));
  }
};