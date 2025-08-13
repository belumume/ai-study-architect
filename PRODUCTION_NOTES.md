# Production Notes - AI Study Architect

## 🔐 Critical Security Information

### Backup Encryption Key
- **Storage**: Saved in Proton Pass as login entry
- **Location**: Render Environment Variables
- **⚠️ NEVER CHANGE**: Changing loses access to ALL previous backups
- **Algorithm**: Fernet (AES-128-CBC + HMAC) - NOT AES-256

### Backup System Status
- **Dual-Provider**: ✅ Fully operational
  - R2: Daily at 2 AM UTC (30-day retention)
  - S3: Weekly Sundays at 3 AM UTC (14-day retention)
- **Restore Tested**: ✅ Successfully verified 2025-08-13
- **Permissions**: ✅ Both buckets private, no public access

## 🚀 Current Production Configuration

### What's Running
- **Live URL**: https://ai-study-architect.onrender.com
- **Platform**: Render Starter Plan ($7/month)
- **Database**: PostgreSQL 17
- **Authentication**: JWT with RS256
- **Backups**: Automated via GitHub Actions

### What's NOT Implemented (By Design)
- **Staging Environment**: Not needed at current scale
- **Feature Flags**: Files exist but not integrated (future use)
- **Sentry Monitoring**: Skipped - using GitHub Actions notifications
- **Complex CI/CD**: Just backup automation for now

## 📝 Development Philosophy

### Current Approach
- **Direct to Production**: Continuous deployment without staging
- **YAGNI Principle**: Build only what's needed now
- **Simple Infrastructure**: Focus on features, not DevOps

### When to Add Infrastructure
| Feature | Add When You Have |
|---------|------------------|
| Staging Environment | 10+ paying users |
| Feature Flags | Need to A/B test |
| Full CI/CD | Multiple developers |
| Monitoring (Sentry) | 100+ active users |

## 🔧 Common Operations

### Manual Backup Trigger
```bash
# R2 Backup
curl -X POST -H "X-Backup-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "r2"}' \
  https://ai-study-architect.onrender.com/api/v1/backup/trigger

# S3 Backup  
curl -X POST -H "X-Backup-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "s3"}' \
  https://ai-study-architect.onrender.com/api/v1/backup/trigger
```

### Restore from Backup
```bash
# 1. Download backup from S3/R2
aws s3 cp s3://ai-study-architect-backup-2025/backups/production/s3/[filename].enc backup.enc

# 2. Decrypt
python backend/scripts/decrypt_backup.py backup.enc backup.sql

# 3. Restore (if needed)
psql DATABASE_URL < backup.sql
```

## ⚠️ Never Change These

1. **BACKUP_ENCRYPTION_KEY** - Breaks all previous backups
2. **Pre-Deploy Command** - Must remain empty in Render
3. **Root Directory** - Must be "backend" in Render
4. **JWT Algorithm** - RS256 is configured everywhere

## 📊 System Health Metrics

As of January 2025:
- **Backup Success Rate**: 100%
- **Database Size**: ~5MB
- **Monthly Backup Cost**: <$0.01
- **Uptime**: Render Starter = no cold starts
- **Security Score**: Production-ready

## 🎯 Next Milestones

Before adding more infrastructure:
1. Get first 10 users
2. Validate product-market fit
3. Only then consider staging/monitoring/CI

Focus: **Ship features, not infrastructure**

---

*Last Updated: January 2025*
*Next Review: April 2025 (quarterly)*