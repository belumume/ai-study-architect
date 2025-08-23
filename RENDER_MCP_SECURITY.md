# Render MCP Server Security Configuration

## 🔐 Security Safeguards Implementation

### 1. Secure Claude Code Configuration

Add this to your Claude Code configuration to require explicit confirmation:

```json
{
  "mcpServers": {
    "render": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-render"
      ],
      "env": {
        "RENDER_API_KEY": "your-api-key-here",
        "MCP_CONFIRMATION_REQUIRED": "true",
        "MCP_DESTRUCTIVE_OPERATIONS": "confirm"
      }
    }
  }
}
```

### 2. Custom System Prompt for Claude Code

When working with infrastructure, always start with this prompt:

```
You are working with production infrastructure. Follow these rules:

1. NEVER modify environment variables without explicit user confirmation
2. NEVER delete or update services without showing the exact changes first
3. ALWAYS show current values before making changes
4. ALWAYS create backups before destructive operations
5. For ANY update operation, first run a GET to show current state

When asked to modify environment variables:
- First, list the current variables (without values for security)
- Show exactly what will change
- Wait for explicit "yes, proceed" confirmation
- Create a backup comment with timestamp

Destructive operations require typing: "I authorize this destructive operation"
```

### 3. Create Read-Only Operations Workflow

For safe monitoring, use these commands that CANNOT cause damage:

```bash
# Safe read-only operations
- mcp__render__list_services
- mcp__render__get_service
- mcp__render__list_logs
- mcp__render__get_metrics
- mcp__render__list_postgres_instances
- mcp__render__get_postgres
- mcp__render__list_deploys
- mcp__render__get_deploy

# DANGEROUS operations (require confirmation)
- mcp__render__update_environment_variables  ⚠️
- mcp__render__update_web_service  ⚠️
- mcp__render__create_* (any create operation)  ⚠️
```

### 4. Environment Variable Protection Script

Create a pre-check script before ANY environment variable updates:

```python
# save_before_update.py
import json
from datetime import datetime

def require_confirmation(service_id, changes):
    """Require explicit confirmation for env var changes."""
    print("⚠️  DESTRUCTIVE OPERATION DETECTED")
    print(f"Service: {service_id}")
    print("Changes to be made:")
    for key, value in changes.items():
        # Mask sensitive values
        masked = value[:3] + "***" if len(value) > 3 else "***"
        print(f"  - {key}: {masked}")
    
    confirmation = input("\nType 'CONFIRM CHANGES' to proceed: ")
    if confirmation != "CONFIRM CHANGES":
        print("❌ Operation cancelled")
        return False
    
    # Create backup record
    backup = {
        "timestamp": datetime.now().isoformat(),
        "service_id": service_id,
        "changes": list(changes.keys())
    }
    
    with open(f"env_change_log_{datetime.now():%Y%m%d_%H%M%S}.json", "w") as f:
        json.dump(backup, f, indent=2)
    
    return True
```

### 5. Render API Key Permissions Strategy

Since Render doesn't support granular permissions, use these strategies:

#### Option A: Separate Monitoring Account (RECOMMENDED)
1. Create a new Render account for monitoring only
2. Invite it as a "Viewer" to your team
3. Use this account's API key for MCP Server
4. Viewers CANNOT modify anything

#### Option B: Manual Approval Workflow
1. Keep full API key but disable auto-deploy
2. Require manual deploy approval in Render dashboard
3. Any changes via API won't auto-deploy

#### Option C: Time-Limited Access
1. Generate API key only when needed
2. Revoke immediately after use
3. Store key in password manager, not in config

### 6. Audit Log Implementation

Track all MCP operations:

```python
# mcp_audit.py
import json
import os
from datetime import datetime

class MCPAuditLog:
    def __init__(self, log_file="mcp_audit.log"):
        self.log_file = log_file
    
    def log_operation(self, operation, params, result):
        """Log every MCP operation for audit trail."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "params": params,
            "result": "success" if result else "failed",
            "user": os.environ.get("USER", "unknown")
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Alert on destructive operations
        if "update" in operation or "delete" in operation:
            print(f"⚠️  AUDIT ALERT: {operation} performed at {entry['timestamp']}")
```

### 7. Emergency Recovery Plan

If environment variables are accidentally modified:

1. **Immediate Recovery** (within 24 hours):
   ```bash
   # Rollback to previous deploy
   curl -X POST https://api.render.com/v1/services/srv-d2aad97diees738qmshg/deploys/{previous-deploy-id}/rollback \
     -H "Authorization: Bearer $RENDER_API_KEY"
   ```

2. **From Backup**:
   - Use the backup file created earlier
   - Manually restore via Render dashboard
   - Or use the restore script below

3. **From GitHub Secrets**:
   - Critical vars are also in GitHub Actions secrets
   - Can be recovered from there if needed

### 8. Restore Script

```python
# restore_env_vars.py
import json
import requests

def restore_env_vars(backup_file, api_key, service_id):
    """Restore environment variables from backup."""
    with open(backup_file, 'r') as f:
        backup = json.load(f)
    
    print(f"Restoring from backup: {backup['timestamp']}")
    response = input("Type 'RESTORE' to confirm: ")
    
    if response != "RESTORE":
        print("Cancelled")
        return
    
    # Use Render API to restore
    headers = {"Authorization": f"Bearer {api_key}"}
    env_vars = [{"key": k, "value": v} for k, v in backup['env_vars'].items()]
    
    # This would update all env vars - implement carefully!
    print("Manual restoration required via Render dashboard")
    print("Copy values from backup file")
```

## 🛡️ Best Practices Summary

1. **NEVER** store API keys in MCP config directly
2. **ALWAYS** backup before any changes
3. **USE** read-only operations whenever possible
4. **REQUIRE** explicit confirmation for updates
5. **LOG** all operations for audit trail
6. **TEST** changes in a staging environment first
7. **MAINTAIN** offline backups of critical configs
8. **ROTATE** API keys regularly
9. **MONITOR** audit logs for unexpected changes
10. **PRACTICE** recovery procedures regularly

## 🚨 Critical Environment Variables - NEVER MODIFY

These should NEVER be changed without extreme caution:

- `DATABASE_URL` - Breaking this disconnects your database
- `BACKUP_ENCRYPTION_KEY` - Changing loses access to ALL backups
- `JWT_SECRET_KEY` - Changing logs out ALL users
- `SECRET_KEY` - Changing invalidates sessions

## 📋 Safe Monitoring Commands

Use these for daily operations without risk:

```bash
# Check service health
mcp: "Show me the health status of ai-study-architect"

# View recent logs
mcp: "Show me the last 50 logs for ai-study-architect"

# Check metrics
mcp: "What's the current CPU and memory usage?"

# List recent deploys
mcp: "Show me the last 5 deployments"

# Check for errors
mcp: "Show any errors from the last hour"
```

## 🔄 Recovery Contacts

If something goes wrong:

1. Render Support: https://render.com/support
2. GitHub repo: https://github.com/belumume/ai-study-architect
3. Backup locations:
   - Cloudflare R2: Daily backups
   - AWS S3: Weekly backups
   - Local: Your backup files

## ⚡ Quick Disable MCP

If you need to immediately disable MCP:

1. Remove from Claude Code settings
2. Or rename the config section
3. Or revoke the API key in Render dashboard

Remember: It's better to be overly cautious with production infrastructure!