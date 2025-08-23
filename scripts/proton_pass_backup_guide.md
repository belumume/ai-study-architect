# Proton Pass Environment Variables Backup Guide

## ✅ You Already Have (in Proton Pass)
- `BACKUP_ENCRYPTION_KEY` - CRITICAL - Never change this!

## 📝 Quick Backup Checklist for Proton Pass

### 1. Create New Secure Note in Proton Pass
**Title**: `Render - AI Study Architect - Env Vars - [TODAY'S DATE]`

### 2. Copy These from Render Dashboard
Go to: https://dashboard.render.com/web/srv-d2aad97diees738qmshg/env

Copy each value and add to your Proton Pass note:

```
=== API KEYS ===
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

=== AWS S3 (Weekly Backups) ===
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_BACKUP_BUCKET=ai-study-architect-backup-2025

=== CLOUDFLARE R2 (Daily Backups) ===
R2_ACCOUNT_ID=xxx
R2_ACCESS_KEY=xxx
R2_SECRET_KEY=xxx
R2_BUCKET=ai-study-architect-backups

=== SECURITY TOKENS ===
BACKUP_TOKEN=xxx (match GitHub secret)
SECRET_KEY=xxx (auto-generated)
JWT_SECRET_KEY=xxx (auto-generated)

=== AUTO-MANAGED ===
DATABASE_URL=(Render manages this - don't copy)
```

### 3. Add Recovery Sources to Same Note

```
=== RECOVERY SOURCES ===
If lost, regenerate from:

ANTHROPIC_API_KEY: https://console.anthropic.com/settings/keys
OPENAI_API_KEY: https://platform.openai.com/api-keys
BACKUP_TOKEN: https://github.com/belumume/ai-study-architect/settings/secrets/actions
AWS: https://console.aws.amazon.com/iam/
Cloudflare R2: https://dash.cloudflare.com/
BACKUP_ENCRYPTION_KEY: [ALREADY IN PROTON PASS - NEVER CHANGE]

Service ID: srv-d2aad97diees738qmshg
Dashboard: https://dashboard.render.com/web/srv-d2aad97diees738qmshg
```

## 🔐 Why This is Secure

✅ **Proton Pass Features**:
- End-to-end encryption
- Zero-knowledge architecture  
- Version history
- Cross-device sync
- 2FA protection (if enabled)
- Encrypted export capability

## 🚨 Critical Reminders

1. **NEVER change `BACKUP_ENCRYPTION_KEY`** - You already have it safe in Proton Pass
2. **DATABASE_URL** - Don't backup, Render manages this
3. **Update backup** when you rotate API keys
4. **Tag the note** in Proton Pass for easy finding (e.g., "render", "production", "api-keys")

## 📅 Backup Schedule

- **Before**: Any MCP Server modifications
- **After**: Rotating any API key
- **Monthly**: Regular security practice
- **Always**: Before major deployments

## 🔄 Quick Verification

After saving to Proton Pass, verify you can see:
- [ ] Both AI API keys (Anthropic + OpenAI)
- [ ] Both backup provider credentials (R2 + S3)  
- [ ] Security tokens (BACKUP_TOKEN, JWT keys)
- [ ] Recovery source links
- [ ] Service ID and dashboard URL

## 🎯 Using with MCP Server

Now when using Render MCP Server:
1. You have full backup in Proton Pass
2. If anything goes wrong, you can restore from Proton Pass
3. Your `BACKUP_ENCRYPTION_KEY` is safe and unchanged
4. Daily R2 + Weekly S3 backups continue working

## 💡 Pro Tip

In Proton Pass, you can:
- Set an alias like "render-env" for quick access
- Add a password if you want double encryption
- Share with trusted team member (encrypted sharing)
- Export encrypted backup to local file if needed