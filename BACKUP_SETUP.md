# Complete Backup Setup Guide

This guide will help you set up enterprise-grade backups with Cloudflare R2 (primary) and AWS S3 (secondary).

## Prerequisites

- Render Starter plan ($7/month) - Required for cron jobs
- Cloudflare account (you have this ✅)
- AWS account with credits (you have this ✅)
- PostgreSQL client tools (for local testing)

## Step 1: Cloudflare R2 Setup (Primary Backup)

### 1.1 Create R2 Bucket

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click **R2** in the left sidebar
3. Click **Create bucket**
4. Name: `ai-study-architect-backups`
5. Location: Automatic (will use closest to your users)
6. Click **Create bucket**

### 1.2 Create API Token

1. In R2 dashboard, click **Manage R2 API Tokens**
2. Click **Create API token**
3. Configure token:
   - **Token name**: `ai-study-architect-backup`
   - **Permissions**: Select `Object Read & Write`
   - **Specify bucket**: Select `ai-study-architect-backups`
   - **TTL**: Leave blank (permanent)
4. Click **Create API Token**
5. **IMPORTANT**: Copy these values immediately:
   ```
   Access Key ID: [Save this]
   Secret Access Key: [Save this]
   ```
6. Find your Account ID:
   - Go to Cloudflare Dashboard home
   - Right sidebar shows Account ID
   - Copy this value

### 1.3 Add to Render Environment

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your `ai-study-architect` service
3. Go to **Environment** tab
4. Add these variables:
   ```
   R2_ACCOUNT_ID=your-cloudflare-account-id
   R2_ACCESS_KEY=your-r2-access-key-id
   R2_SECRET_KEY=your-r2-secret-access-key
   R2_BUCKET=ai-study-architect-backups
   ```

## Step 2: AWS S3 Setup (Secondary Backup)

### 2.1 Create S3 Bucket

1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com)
2. Click **Create bucket**
3. Configure:
   - **Bucket name**: `ai-study-architect-backup-secondary`
   - **Region**: `us-west-2` (different from Render's oregon/us-west-1)
   - **Object Ownership**: ACLs disabled
   - **Block Public Access**: Block all public access ✅
   - **Versioning**: Enable (for extra safety)
   - **Encryption**: Enable with SSE-S3
4. Click **Create bucket**

### 2.2 Create IAM User for Backups

1. Go to [IAM Console](https://console.aws.amazon.com/iam)
2. Click **Users** → **Add users**
3. User name: `ai-study-architect-backup`
4. Select **Programmatic access**
5. Click **Next: Permissions**
6. Click **Create policy** (opens new tab):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::ai-study-architect-backup-secondary",
           "arn:aws:s3:::ai-study-architect-backup-secondary/*"
         ]
       }
     ]
   }
   ```
7. Name policy: `AIStudyArchitectBackupPolicy`
8. Back in user creation, select this policy
9. Create user and **save credentials**:
   ```
   Access key ID: [Save this]
   Secret access key: [Save this]
   ```

### 2.3 Add to Render Environment

Add these to your Render environment variables:
```
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-west-2
AWS_BACKUP_BUCKET=ai-study-architect-backup-secondary
```

## Step 3: Generate Encryption Key

1. On your local machine (Git Bash, WSL, or Linux):
   ```bash
   openssl rand -base64 32
   ```
2. Copy the output
3. Add to Render environment:
   ```
   BACKUP_ENCRYPTION_KEY=the-generated-key
   ```

## Step 4: Set Up Cron Jobs in Render

### Option A: Using Render Dashboard (Easier)

1. Go to Render Dashboard
2. Click **New +** → **Background Worker**
3. Connect your GitHub repository
4. Configure Daily R2 Backup:
   - **Name**: `backup-primary-r2`
   - **Environment**: Python 3
   - **Build Command**: `cd backend && pip install boto3 cryptography`
   - **Start Command**: `cd backend && python scripts/backup_database.py --r2`
5. After creation, go to Settings:
   - Change type to **Cron Job**
   - Set schedule: `0 2 * * *` (2 AM UTC daily)
   - Copy all environment variables from main service

6. Repeat for Weekly S3 Backup:
   - **Name**: `backup-secondary-s3`
   - **Start Command**: `cd backend && python scripts/backup_database.py --s3`
   - **Schedule**: `0 3 * * 0` (3 AM UTC Sundays)

### Option B: Using render.yaml (Infrastructure as Code)

Use the `render-crons.yaml` file we created, but note that cron jobs in render.yaml are still in beta.

## Step 5: Test Backups Manually

### Test R2 Backup
```bash
cd backend
python scripts/backup_database.py --r2
```

### Test S3 Backup
```bash
cd backend
python scripts/backup_database.py --s3
```

### Show Setup Instructions
```bash
python scripts/backup_database.py --setup
```

## Step 6: Set Up Monitoring (Optional)

### Sentry Integration
1. Sign up at [Sentry.io](https://sentry.io) (free)
2. Create a Python project
3. Add to Render environment:
   ```
   SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
   ```

### Slack/Discord Alerts
1. Create webhook URL in your Slack/Discord
2. Add to Render environment:
   ```
   BACKUP_ALERT_WEBHOOK=https://hooks.slack.com/services/xxx
   ```

## Step 7: Verify Everything Works

1. Check R2 bucket:
   - Go to Cloudflare Dashboard > R2
   - Click your bucket
   - Should see backup files after first run

2. Check S3 bucket:
   - Go to AWS S3 Console
   - Click your bucket
   - Check `backups/production/aws_s3/` folder

3. Check Render logs:
   - Go to Render Dashboard
   - Select cron job service
   - Check Logs tab for execution history

## Backup Schedule

- **Daily at 2 AM UTC**: Cloudflare R2 (Primary)
- **Weekly on Sunday at 3 AM UTC**: AWS S3 (Secondary)
- **Retention**: 30 days for R2, 14 days for S3
- **Minimum kept**: 7 backups for R2, 3 for S3

## Cost Breakdown

### Monthly Costs
- **Render Cron Jobs**: Included in $7/month Starter plan
- **Cloudflare R2**: FREE (under 10GB)
- **AWS S3**: ~$0.02/month (using credits first 3 months)
- **Total**: $7.02/month

### Storage Usage (Estimated)
- Database size: ~10MB initially
- Daily backups: 10MB × 30 = 300MB
- Weekly backups: 10MB × 4 = 40MB
- **Total**: ~340MB (well under free tiers)

## Troubleshooting

### "pg_dump not found"
- Render includes PostgreSQL client tools
- For local testing, install: `apt-get install postgresql-client`

### "Access Denied" errors
- Double-check API keys are correct
- Ensure bucket names match exactly
- Verify IAM permissions (AWS) or token permissions (R2)

### Backup seems to hang
- Normal for first backup (building indices)
- Check DATABASE_URL is accessible
- Timeout is set to 5 minutes

### Encryption key lost
- Generate new one, but old backups won't be restorable
- Keep key in password manager

## Recovery Process

### From Cloudflare R2
1. Download backup from R2 dashboard
2. Decrypt using your encryption key
3. Restore using pg_restore

### From AWS S3
1. Download from S3 console
2. Decrypt using your encryption key
3. Restore using pg_restore

### Emergency Contacts
- **Your email**: For backup alerts
- **Render Support**: support@render.com
- **Status Pages**: 
  - https://status.render.com
  - https://www.cloudflarestatus.com
  - https://status.aws.amazon.com

## Next Steps

1. ✅ Complete R2 setup
2. ✅ Complete S3 setup
3. ✅ Add encryption key
4. ✅ Deploy cron jobs
5. ✅ Test manual backups
6. ⏰ Wait for first automated backup
7. 📊 Monitor for a week
8. 🎉 Sleep better knowing your data is safe!

---

Remember: The best backup is the one you never need, but when you need it, you'll be glad it's there!