# Backup Security - Real Threats & Mitigations

## Our Encryption Choice: Fernet (AES-128 + HMAC)

We use **Fernet** for backup encryption, which provides:
- **AES-128-CBC** encryption (unbreakable with current technology)
- **HMAC** authentication (prevents tampering)
- **Automatic IV/nonce handling** (prevents reuse vulnerabilities)
- **Simple API** (hard to misconfigure)

### Why Not AES-256?

After careful consideration and expert consultation:
1. **No practical security difference** - Both AES-128 and AES-256 are computationally unbreakable
2. **Fernet includes authentication** - More important than key size for backup integrity
3. **Simpler = more secure** - Complex implementations introduce vulnerabilities
4. **Battle-tested** - Fernet is widely used and well-vetted

## Real Security Threats & How We Address Them

### 1. 🔑 Key Management (HIGHEST RISK)

**Threat**: Lost or leaked encryption keys
**Our Mitigation**:
- Keys stored in Render environment variables (not in code)
- Separate from backup storage (not in R2/S3)
- Never logged or transmitted

**Action Items**:
- [ ] Document key in secure password manager
- [ ] Create key backup in separate secure location
- [ ] Never change `BACKUP_ENCRYPTION_KEY` (will lose access to old backups)

### 2. 🔄 Restore Testing (CRITICAL)

**Threat**: Backups that can't be restored are useless
**Current Status**: Not tested yet

**Testing Procedure** (Do quarterly):
```bash
# 1. Download a recent backup
aws s3 cp s3://ai-study-architect-backup-2025/backups/production/s3/[recent-backup].enc test-backup.enc

# 2. Decrypt using the provided script
# Option A: Use the decrypt script in the repo
python backend/scripts/decrypt_backup.py test-backup.enc test-backup.sql

# Option B: Set environment variable first
export BACKUP_ENCRYPTION_KEY='your-key-from-render'
python backend/scripts/decrypt_backup.py test-backup.enc test-backup.sql

# 3. Verify SQL is valid
head -n 100 test-backup.sql  # Should see valid PostgreSQL dump

# 4. (Optional) Restore to test database
createdb test_restore
psql test_restore < test-backup.sql
dropdb test_restore

# 5. Clean up
rm test-backup.enc test-backup.sql
```

### 3. 🔒 Cloud Permissions

**Threat**: Overly permissive bucket access
**Our Mitigation**:
- R2 bucket is private (no public access)
- S3 bucket is private (no public access)
- API tokens have minimal required permissions

**Verification**:
```bash
# Check R2 bucket (via Cloudflare dashboard)
# Ensure "Public Access" is DISABLED

# Check S3 bucket
aws s3api get-bucket-acl --bucket ai-study-architect-backup-2025
# Should show only owner has FULL_CONTROL
```

### 4. 📊 Backup Monitoring

**Threat**: Silent backup failures
**Our Mitigation**:
- GitHub Actions emails on failure
- Logs available in Render dashboard
- Manual status check endpoint

**Quick Health Check**:
```bash
# Check last backup status
curl -H "X-Backup-Token: YOUR_TOKEN" \
  https://ai-study-architect.onrender.com/api/v1/backup/status

# View GitHub Actions history
# https://github.com/belumume/ai-study-architect/actions
```

### 5. 🔄 Key Rotation Strategy

**Current**: No rotation (changing key loses access to old backups)

**Future Consideration** (when you have real users):
1. Generate new key annually
2. Re-encrypt recent backups with new key
3. Keep old key for emergency access to old backups
4. Document both keys securely

### 6. 🚨 Insider Threats

**Threat**: Anyone with Render access can see encryption keys
**Mitigation**:
- Limit Render team access
- Use Render's audit logs
- Consider moving to dedicated key management (AWS KMS, HashiCorp Vault) when you scale

## Security Checklist

### Immediate Actions
- [x] Backups are encrypted (Fernet/AES-128)
- [x] Keys stored separately from backups
- [x] Private buckets (no public access)
- [x] Rate limiting on backup endpoint
- [x] Automated backups running

### Before Launch
- [ ] Test restore procedure
- [ ] Document encryption key in password manager
- [ ] Verify bucket permissions
- [ ] Create runbook for emergency restore

### Quarterly Reviews
- [ ] Test restore from both R2 and S3
- [ ] Review access logs
- [ ] Check for unused API keys
- [ ] Update this documentation

## Emergency Contacts

- **Render Support**: https://render.com/support
- **AWS Support**: AWS Console → Support Center
- **Cloudflare Support**: https://dash.cloudflare.com/?to=/:account/support

## The Bottom Line

Your backups are **cryptographically secure**. The real risks are operational:
1. **Losing the encryption key** → Keep secure backups of the key
2. **Not testing restores** → Test quarterly
3. **Misconfigured permissions** → Review regularly
4. **Silent failures** → Monitor GitHub Actions

Focus on these operational security measures rather than cryptographic improvements. Your Fernet encryption is already unbreakable - make sure your processes are too!

---

*Last Updated: January 2025*
*Encryption: Fernet (AES-128-CBC + HMAC)*
*Never change BACKUP_ENCRYPTION_KEY once set!*