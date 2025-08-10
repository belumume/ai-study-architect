"""
Comprehensive security headers middleware for FastAPI
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
import hashlib
import secrets
import base64


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to all responses.
    
    This implements OWASP recommended security headers:
    https://owasp.org/www-project-secure-headers/
    """
    
    def __init__(
        self, 
        app,
        is_debug: bool = False,
        nonce_enabled: bool = True,
        report_uri: Optional[str] = None
    ):
        super().__init__(app)
        self.is_debug = is_debug
        self.nonce_enabled = nonce_enabled
        self.report_uri = report_uri
        
    async def dispatch(self, request: Request, call_next):
        # Generate nonce for CSP if enabled
        nonce = None
        if self.nonce_enabled:
            nonce = base64.b64encode(secrets.token_bytes(16)).decode('utf-8')
            request.state.csp_nonce = nonce
        
        # Process request
        response = await call_next(request)
        
        # Check if this is a documentation endpoint
        is_docs_endpoint = request.url.path in ["/docs", "/redoc", "/openapi.json"]
        
        # Add security headers
        self._add_security_headers(response, nonce, is_docs_endpoint)
        
        return response
    
    def _add_security_headers(self, response: Response, nonce: Optional[str] = None, is_docs_endpoint: bool = False) -> None:
        """Add comprehensive security headers to response"""
        
        # 1. Content-Type Options - Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 2. Frame Options - Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # 3. XSS Protection - Enable XSS filter (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 4. HSTS - Force HTTPS
        if not self.is_debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"  # 2 years
            )
        else:
            # Shorter duration for development
            response.headers["Strict-Transport-Security"] = (
                "max-age=3600"  # 1 hour
            )
        
        # 5. Referrer Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 6. Permissions Policy - Control browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), ambient-light-sensor=(), autoplay=(), battery=(), "
            "camera=(), cross-origin-isolated=(), display-capture=(), "
            "document-domain=(), encrypted-media=(), execution-while-not-rendered=(), "
            "execution-while-out-of-viewport=(), fullscreen=(self), geolocation=(), "
            "gyroscope=(), keyboard-map=(), magnetometer=(), microphone=(), "
            "midi=(), navigation-override=(), payment=(), picture-in-picture=(), "
            "publickey-credentials-get=(), screen-wake-lock=(), sync-xhr=(), "
            "usb=(), web-share=(), xr-spatial-tracking=()"
        )
        
        # 7. Cache Control - Prevent caching of sensitive data
        if response.headers.get("Cache-Control") is None:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        
        # 8. Content Security Policy
        csp_directives = self._get_csp_directives(nonce, is_docs_endpoint)
        csp_header = "; ".join([f"{k} {v}" for k, v in csp_directives.items()])
        
        if self.report_uri:
            csp_header += f"; report-uri {self.report_uri}"
            
        response.headers["Content-Security-Policy"] = csp_header
        
        # 9. Cross-Origin Headers
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # 10. Additional Security Headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-Download-Options"] = "noopen"
        response.headers["X-DNS-Prefetch-Control"] = "off"
        
        # 11. Remove sensitive headers
        headers_to_remove = ["Server", "X-Powered-By", "X-AspNet-Version"]
        for header in headers_to_remove:
            if header in response.headers:
                del response.headers[header]
    
    def _get_csp_directives(self, nonce: Optional[str] = None, is_docs_endpoint: bool = False) -> Dict[str, str]:
        """Get CSP directives based on environment"""
        
        # Special handling for documentation endpoints (Swagger/ReDoc)
        if is_docs_endpoint:
            return {
                "default-src": "'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com",
                "script-src": "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
                "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "img-src": "'self' data: https: blob:",
                "font-src": "'self' data: https://cdn.jsdelivr.net",
                "connect-src": "'self'",
                "frame-ancestors": "'none'",
                "form-action": "'self'",
                "base-uri": "'self'",
                "object-src": "'none'",
                "media-src": "'self'",
                "manifest-src": "'self'",
                "worker-src": "'self' blob:",
                "child-src": "'self' blob:",
                "frame-src": "'none'"
            }
        
        if self.is_debug:
            # Relaxed CSP for development (Swagger UI support)
            script_src = "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net"
            if nonce:
                script_src = f"'self' 'nonce-{nonce}' 'unsafe-eval' https://cdn.jsdelivr.net"
                
            return {
                "default-src": "'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com",
                "script-src": script_src,
                "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "img-src": "'self' data: https: blob:",
                "font-src": "'self' data: https://cdn.jsdelivr.net",
                "connect-src": "'self' https://cdn.jsdelivr.net",
                "frame-ancestors": "'none'",
                "form-action": "'self'",
                "base-uri": "'self'",
                "object-src": "'none'",
                "media-src": "'self'",
                "manifest-src": "'self'",
                "worker-src": "'self' blob:",
                "child-src": "'self' blob:",
                "frame-src": "'none'"
            }
        else:
            # Strict CSP for production
            script_src = "'self'"
            if nonce:
                script_src = f"'self' 'nonce-{nonce}'"
                
            return {
                "default-src": "'none'",
                "script-src": script_src,
                "style-src": "'self'",
                "img-src": "'self' data:",
                "font-src": "'self'",
                "connect-src": "'self'",
                "frame-ancestors": "'none'",
                "form-action": "'self'",
                "base-uri": "'self'",
                "object-src": "'none'",
                "media-src": "'self'",
                "manifest-src": "'self'",
                "worker-src": "'none'",
                "child-src": "'none'",
                "frame-src": "'none'",
                "upgrade-insecure-requests": ""
            }


def get_csp_nonce(request: Request) -> Optional[str]:
    """Get CSP nonce from request state"""
    return getattr(request.state, "csp_nonce", None)