"""
Monitoring setup for AI Study Architect.
Uses Sentry (free tier) for error tracking and performance monitoring.

To set up:
1. Sign up at https://sentry.io (free)
2. Create a new project (Python/FastAPI)
3. Copy your DSN
4. Set SENTRY_DSN environment variable
"""

import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Only import sentry_sdk if DSN is configured
sentry_sdk = None
if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning("Sentry SDK not installed. Run: pip install sentry-sdk")
        sentry_sdk = None

def init_monitoring(app=None):
    """Initialize monitoring services"""
    
    if not sentry_sdk:
        logger.info("Sentry monitoring not configured (no DSN or SDK)")
        return
    
    if not hasattr(settings, 'SENTRY_DSN') or not settings.SENTRY_DSN:
        logger.info("Sentry monitoring disabled (no SENTRY_DSN)")
        return
    
    try:
        # Configure Sentry
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            profiles_sample_rate=0.1,  # 10% profiling
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",
                    failed_request_status_codes=[500, 503],
                ),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
            before_send=before_send_filter,
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            release=get_release_version(),
        )
        
        logger.info(f"✅ Sentry monitoring initialized for {settings.ENVIRONMENT}")
        
        # Test by capturing a message
        if settings.ENVIRONMENT == "development":
            sentry_sdk.capture_message("Sentry integration test", level="info")
            
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")

def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry.
    Removes sensitive data and filters out noise.
    """
    
    # Filter out certain errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # Don't send client disconnection errors
        if exc_type.__name__ in ['ClientDisconnect', 'ConnectionResetError']:
            return None
        
        # Don't send rate limit errors (they're expected)
        if exc_type.__name__ == 'RateLimitExceeded':
            return None
    
    # Remove sensitive data from request
    if 'request' in event and 'data' in event['request']:
        # Remove passwords and tokens
        if isinstance(event['request']['data'], dict):
            for key in ['password', 'token', 'api_key', 'secret']:
                if key in event['request']['data']:
                    event['request']['data'][key] = '[FILTERED]'
    
    # Add custom context
    event['contexts']['app'] = {
        'environment': settings.ENVIRONMENT,
        'api_version': '0.1.0',
    }
    
    return event

def get_release_version() -> Optional[str]:
    """Get the current release version from git or environment"""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'describe', '--tags', '--always'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None

def capture_exception(error: Exception, context: Optional[dict] = None):
    """Manually capture an exception with context"""
    if sentry_sdk:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_exception(error)
    else:
        # Fallback to logging
        logger.error(f"Exception: {error}", exc_info=True, extra=context)

def capture_message(message: str, level: str = "info", context: Optional[dict] = None):
    """Capture a message/event"""
    if sentry_sdk:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_message(message, level=level)
    else:
        # Fallback to logging
        log_func = getattr(logger, level, logger.info)
        log_func(message, extra=context)

def send_backup_alert(backup_status: dict):
    """Send alert for backup status (success or failure)"""
    import os
    
    if not backup_status.get("providers"):
        return
    
    all_success = all(p["success"] for p in backup_status["providers"].values())
    
    if all_success:
        # Log success (don't alert on success to avoid noise)
        logger.info(f"✅ All backups successful: {backup_status}")
    else:
        # Alert on failure
        failed_providers = [
            name for name, info in backup_status["providers"].items()
            if not info["success"]
        ]
        
        message = f"Backup failure: {', '.join(failed_providers)}"
        
        # Send to Sentry if configured
        capture_message(message, level="error", context=backup_status)
        
        # Also send webhook if configured (Slack, Discord, etc.)
        webhook_url = os.getenv("BACKUP_ALERT_WEBHOOK")
        if webhook_url:
            try:
                import requests
                payload = {
                    "text": f"🚨 Backup Alert",
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Backup Failure Detected*\n"
                                   f"Environment: {backup_status.get('environment', 'unknown')}\n"
                                   f"Failed: {', '.join(failed_providers)}\n"
                                   f"Time: {backup_status.get('timestamp', 'unknown')}"
                        }
                    }]
                }
                requests.post(webhook_url, json=payload, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")

def track_performance(transaction_name: str):
    """
    Performance monitoring decorator.
    
    Usage:
        @track_performance("process_content")
        async def process_content(file):
            # ... processing logic
    """
    def decorator(func):
        if not sentry_sdk:
            return func
            
        async def async_wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op="function", name=transaction_name):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op="function", name=transaction_name):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Usage in your code:
"""
from app.core.monitoring import capture_exception, track_performance

# Capture exceptions with context
try:
    result = risky_operation()
except Exception as e:
    capture_exception(e, context={
        "user_id": user_id,
        "operation": "file_upload",
        "file_size": file_size
    })
    raise

# Track performance
@track_performance("ai_generation")
async def generate_response(prompt):
    # This will be tracked in Sentry's performance monitoring
    response = await ai_service.generate(prompt)
    return response
"""