"""
Additional security recommendations for admin endpoints
"""

# 1. Hide admin endpoints from public OpenAPI docs
# Add this to admin.py router definition:
# router = APIRouter(include_in_schema=False)  # Hides from /docs

# 2. Add IP allowlist for admin endpoints (optional)
ADMIN_ALLOWED_IPS = [
    "127.0.0.1",  # localhost
    # Add your home/office IP here
]

def check_admin_ip(request_ip: str) -> bool:
    """Check if IP is allowed to access admin endpoints"""
    return request_ip in ADMIN_ALLOWED_IPS

# 3. Add admin action audit logging
def log_admin_action(admin_email: str, action: str, details: dict):
    """Log all admin actions for audit trail"""
    # Log to file or database
    pass

# 4. Consider moving admin to separate subdomain
# admin.aistudyarchitect.com with additional auth layer