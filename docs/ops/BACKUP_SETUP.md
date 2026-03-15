# AI Study Architect - Complete Backup System Documentation

## Overview

The AI Study Architect implements a **dual-provider backup strategy** for maximum reliability:

| Provider | Schedule | Retention | Purpose |
|----------|----------|-----------|---------|
| **Cloudflare R2** (Primary) | Daily at 2 AM UTC | 30 days, min 7 backups | Cost-effective daily backups |
| **AWS S3** (Secondary) | Weekly (Sundays) at 3 AM UTC | 14 days, min 3 backups | Redundant weekly snapshots |

## Secrets Configuration

All backup secrets are stored in **GitHub Actions Secrets** (not in code or .env files).

### GitHub Actions Secrets Required
```
BACKUP_TOKEN              # Auth token for backup endpoints
BACKUP_ENCRYPTION_KEY     # Fernet key for backup encryption - DO NOT CHANGE
```

### AWS S3 Secrets
```
AWS_ACCESS_KEY_ID         # IAM user: ai-study-architect-user
AWS_SECRET_ACCESS_KEY     # Rotated March 2026
AWS_BACKUP_BUCKET         # ai-study-architect-backup-2025
AWS_REGION                # us-west-2 (default)
```

### Cloudflare R2 Secrets
```
R2_ACCOUNT_ID             # Cloudflare Account ID
R2_ACCESS_KEY             # From R2 API token
R2_SECRET_KEY             # From R2 API token
R2_BUCKET                 # ai-study-architect-backups
```

### Backend (CF Container) Secrets
```
DATABASE_URL              # Neon PostgreSQL connection string (used by backup script)
```

## Automated Backup Schedule

GitHub Actions (`.github/workflows/backup.yml`) automatically triggers backups:

| Time | Day | Provider | Frequency |
|------|-----|----------|-----------|
| 2:00 AM UTC | Mon-Sat | R2 | Daily |
| 2:00 AM UTC | Sunday | R2 | Daily |
| 3:00 AM UTC | Sunday | S3 | Weekly |

## Manual Backup Triggers

```bash
# Trigger R2 backup
gh workflow run backup.yml --field provider=r2

# Trigger S3 backup
gh workflow run backup.yml --field provider=s3

# Trigger both providers
gh workflow run backup.yml --field provider=both

# Check recent backup runs
gh run list --workflow=backup.yml --limit=5
```

Or via the backup API endpoint:
```bash
# Test configuration
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://aistudyarchitect.com/api/v1/backup/test

# Check backup status
curl -X GET -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://aistudyarchitect.com/api/v1/backup/status

# Trigger manual backup (rate-limited to 1/hour)
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "r2"}' \
  https://aistudyarchitect.com/api/v1/backup/trigger
```

## Monitoring Backups

### View Recent Backup Logs

1. **GitHub Actions**: [View Workflow Runs](https://github.com/belumume/ai-study-architect/actions/workflows/backup.yml)
2. **Container logs**: `npx wrangler logs --deployment-id <id>` or Cloudflare Dashboard

### Check Backup Files

**Cloudflare R2:**
1. Go to [Cloudflare R2 Dashboard](https://dash.cloudflare.com/?to=/:account/r2/buckets)
2. Click on `ai-study-architect-backups` bucket
3. Files are organized by date: `backup_20260315_020000.sql.enc`

**AWS S3:**
1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com/s3/buckets)
2. Click on `ai-study-architect-backup-2025` bucket
3. Files are organized by date: `backup_20260316_030000.sql.enc`

## Security Features

- **Token Authentication**: All backup endpoints require `X-Backup-Token` header
- **Fernet Encryption (AES-128 + HMAC)**: All backups encrypted AND authenticated before upload
- **Rate Limiting**: 1-hour cooldown for manual triggers
- **Automatic Cleanup**: Old backups deleted based on retention policy
- **Private Buckets**: Both R2 and S3 buckets are private, no public access
- **S3 credential guard**: backup.yml skips S3 step if `AWS_ACCESS_KEY_ID` secret is not set

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "R2 not configured" | Check R2 secrets in GitHub Actions |
| "Invalid credentials" | Verify R2_ACCESS_KEY and R2_SECRET_KEY |
| "Bucket not found" | Ensure R2_BUCKET matches your Cloudflare bucket name |
| "Rate limit exceeded" | Wait 1 hour between manual backups |
| "Backup failed" | Check GitHub Actions logs or container logs |
| S3 step skipped | Verify AWS_ACCESS_KEY_ID is set in GitHub Secrets |

### Debug Commands

```bash
# Detailed configuration test
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://aistudyarchitect.com/api/v1/backup/debug

# Check which backup script locations exist
curl -X POST -H "X-Backup-Token: YOUR_BACKUP_TOKEN" \
  https://aistudyarchitect.com/api/v1/backup/test
```

## Backup Retention Policies

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

## Cost Estimation

For a 100MB database:

| Provider | Monthly Storage | Egress | API Calls | Total |
|----------|----------------|--------|-----------|-------|
| R2 | $0.015 | $0 (free) | $0.01 | ~$0.03 |
| S3 | $0.002 | $0.09/GB | $0.01 | ~$0.10 |

**Total monthly cost**: ~$0.13 for dual-provider redundancy

## Manual Recovery Process

If you need to restore from backup:

```bash
# 1. List available backups
aws s3 ls s3://ai-study-architect-backup-2025/
# or for R2
aws s3 ls s3://ai-study-architect-backups/ --endpoint-url https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com

# 2. Download backup
aws s3 cp s3://bucket-name/backup_20260315_020000.sql.enc backup.sql.enc

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

## Future Enhancements

- [ ] Slack/Discord notifications on backup failure
- [ ] Prometheus metrics for backup monitoring
- [ ] Point-in-time recovery with WAL archiving
- [ ] Cross-region replication for R2/S3
- [ ] Automated restore testing

## Best Practices

1. **Never change BACKUP_ENCRYPTION_KEY** - You'll lose ability to decrypt old backups
2. **Test recovery process quarterly** - Ensure backups are actually restorable
3. **Monitor GitHub Actions** - Set up email alerts for workflow failures
4. **Keep credentials secure** - Use GitHub Secrets only (never in code or .env)
5. **Rotate AWS keys periodically** - Last rotation: March 2026
6. **Document everything** - Update this file when making changes

---

*Last updated: March 2026*
*Backup system version: 3.0 (CF Container + GitHub Actions, dual-provider R2 + S3)*