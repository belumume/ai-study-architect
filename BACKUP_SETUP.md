# AI Study Architect - Complete Backup System Documentation

## 🚀 Overview

The AI Study Architect implements a **dual-provider backup strategy** for maximum reliability:

| Provider | Schedule | Retention | Purpose |
|----------|----------|-----------|---------|
| **Cloudflare R2** (Primary) | Daily at 2 AM UTC | 30 days, min 7 backups | Cost-effective daily backups |
| **AWS S3** (Secondary) | Weekly (Sundays) at 3 AM UTC | 14 days, min 3 backups | Redundant weekly snapshots |

## 🔑 Required Environment Variables in Render

### Core Configuration (Already Set ✅)
```bash
BACKUP_TOKEN=<your-secure-token>              # Already configured
BACKUP_ENCRYPTION_KEY=<your-encryption-key>   # Already configured - DO NOT CHANGE
DATABASE_URL=postgresql://...                 # Auto-configured by Render
```

### AWS S3 Configuration (Already Working ✅)
```bash
AWS_ACCESS_KEY_ID=<your-aws-key>             # Already configured
AWS_SECRET_ACCESS_KEY=<your-aws-secret>      # Already configured  
AWS_BACKUP_BUCKET=ai-study-architect-backup-2025  # Already configured
AWS_REGION=us-west-2                         # Optional, defaults to us-west-2
```

### Cloudflare R2 Configuration (Add These Now 🔴)
```bash
R2_ACCOUNT_ID=364ef23a3db274c2248c90746f777     # Your Cloudflare Account ID
R2_ACCESS_KEY=<from-cloudflare-dashboard>       # From R2 API token creation
R2_SECRET_KEY=<from-cloudflare-dashboard>       # From R2 API token creation
R2_BUCKET=ai-study-architect-backups            # Your R2 bucket name
```

## 📋 Step-by-Step R2 Setup

### Step 1: Add R2 Credentials to Render

1. Go to [Render Dashboard](https://dashboard.render.com/web/srv-ctgfttbtq21c73b0pd60/env)
2. Click **Add Environment Variable** for each:
   - `R2_ACCOUNT_ID` = `364ef23a3db274c2248c90746f777`
   - `R2_ACCESS_KEY` = (from your Cloudflare R2 API token)
   - `R2_SECRET_KEY` = (from your Cloudflare R2 API token)  
   - `R2_BUCKET` = `ai-study-architect-backups`
3. Click **Save Changes**
4. Wait for automatic redeploy (takes ~2-3 minutes)

### Step 2: Test R2 Configuration

After Render redeploys, test the configuration:

```bash
# Test configuration (checks if all settings are correct)
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/test

# Check backup status
curl -X GET -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/status
```

Expected response should show:
```json
{
  "r2_configured": true,
  "r2_client_creation": "success",
  "aws_configured": true
}
```

### Step 3: Test Manual R2 Backup

```bash
# Trigger R2 backup manually
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "r2"}' \
  https://ai-study-architect.onrender.com/api/v1/backup/trigger
```

### Step 4: Test Both Providers

```bash
# Trigger both providers simultaneously
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "both"}' \
  https://ai-study-architect.onrender.com/api/v1/backup/trigger
```

## 🔄 Automated Backup Schedule

GitHub Actions automatically triggers backups:

| Time | Day | Provider | Frequency |
|------|-----|----------|-----------|
| 2:00 AM UTC | Mon-Sat | R2 | Daily |
| 2:00 AM UTC | Sunday | R2 | Daily |
| 3:00 AM UTC | Sunday | S3 | Weekly |

**Note**: GitHub Actions bypasses rate limiting. Manual triggers are limited to once per hour.

## 🔍 Monitoring Backups

### View Recent Backup Logs

1. **GitHub Actions**: [View Workflow Runs](https://github.com/belumume/ai-study-architect/actions/workflows/backup.yml)
2. **Render Logs**: Dashboard → ai-study-architect → Logs

### Check Backup Files

**Cloudflare R2:**
1. Go to [Cloudflare R2 Dashboard](https://dash.cloudflare.com/?to=/:account/r2/buckets)
2. Click on `ai-study-architect-backups` bucket
3. Files are organized by date: `backup_20250113_020000.sql.enc`

**AWS S3:**
1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com/s3/buckets)
2. Click on `ai-study-architect-backup-2025` bucket
3. Files are organized by date: `backup_20250113_030000.sql.enc`

## 🔐 Security Features

- ✅ **Token Authentication**: All backup endpoints require `X-Backup-Token` header
- ✅ **AES-256 Encryption**: All backups encrypted before upload
- ✅ **Rate Limiting**: 1-hour cooldown for manual triggers (bypassed for GitHub Actions)
- ✅ **Automatic Cleanup**: Old backups deleted based on retention policy
- ✅ **Private Buckets**: Both R2 and S3 buckets are private, no public access

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "R2 not configured" | Add R2 environment variables to Render |
| "Invalid credentials" | Check R2_ACCESS_KEY and R2_SECRET_KEY are correct |
| "Bucket not found" | Ensure R2_BUCKET matches your Cloudflare bucket name |
| "Rate limit exceeded" | Wait 1 hour between manual backups |
| "Backup failed" | Check Render logs for detailed error messages |

### Debug Commands

```bash
# Detailed configuration test
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/debug

# Check which backup script locations exist
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/test
```

## 🔄 Backup Retention Policies

### Cloudflare R2 (Primary)
- **Retention**: 30 days
- **Minimum backups**: 7 (keeps last week even if older than 30 days)
- **Storage cost**: ~$0.015/GB/month
- **Frequency**: Daily

### AWS S3 (Secondary)  
- **Retention**: 14 days
- **Minimum backups**: 3
- **Storage cost**: ~$0.023/GB/month (S3 Standard)
- **Frequency**: Weekly

### Automatic Cleanup
The backup script automatically deletes old backups when:
1. Backup is older than retention period AND
2. More than minimum number of backups exist

## 📊 Cost Estimation

For a 100MB database:

| Provider | Monthly Storage | Egress | API Calls | Total |
|----------|----------------|--------|-----------|-------|
| R2 | $0.015 | $0 (free) | $0.01 | ~$0.03 |
| S3 | $0.002 | $0.09/GB | $0.01 | ~$0.10 |

**Total monthly cost**: ~$0.13 for dual-provider redundancy

## 🚨 Manual Recovery Process

If you need to restore from backup:

```bash
# 1. List available backups
aws s3 ls s3://ai-study-architect-backup-2025/
# or for R2
aws s3 ls s3://ai-study-architect-backups/ --endpoint-url https://364ef23a3db274c2248c90746f777.r2.cloudflarestorage.com

# 2. Download backup
aws s3 cp s3://bucket-name/backup_20250113_020000.sql.enc backup.sql.enc

# 3. Decrypt backup
python -c "
from cryptography.fernet import Fernet
import sys
key = 'YOUR_BACKUP_ENCRYPTION_KEY'
f = Fernet(key.encode())
with open('backup.sql.enc', 'rb') as file:
    encrypted = file.read()
decrypted = f.decrypt(encrypted)
with open('backup.sql', 'wb') as file:
    file.write(decrypted)
print('Decrypted successfully')
"

# 4. Restore to database
psql YOUR_DATABASE_URL < backup.sql
```

## 📈 Future Enhancements

- [ ] Slack/Discord notifications on backup failure
- [ ] Prometheus metrics for backup monitoring
- [ ] Point-in-time recovery with WAL archiving
- [ ] Cross-region replication for R2/S3
- [ ] Automated restore testing

## 💡 Best Practices

1. **Never change BACKUP_ENCRYPTION_KEY** - You'll lose ability to decrypt old backups
2. **Test recovery process quarterly** - Ensure backups are actually restorable
3. **Monitor GitHub Actions** - Set up email alerts for workflow failures
4. **Keep credentials secure** - Use GitHub Secrets and Render environment variables
5. **Document everything** - Update this file when making changes

---

*Last updated: January 2025*
*Backup system version: 2.0 (Dual-provider with R2 + S3)*