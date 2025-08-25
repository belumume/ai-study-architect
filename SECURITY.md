# Security & Privacy Guidelines for AI Study Architect

## Overview

This document outlines security best practices for the AI Study Architect project. As an educational AI platform handling student data, we implement comprehensive security measures and follow industry standards.

## Data Classification

### 🔴 CRITICAL - Never Commit to Git
- **Student Personal Data**: Names, emails, student IDs, grades
- **Study Materials**: Uploaded PDFs, notes, recordings, assignments
- **AI Processing Data**: Embeddings, cached responses containing user content
- **Authentication Tokens**: API keys, OAuth tokens, JWT secrets
- **Database Dumps**: Any exports containing user data

### 🟡 SENSITIVE - Requires Careful Handling
- **Model Checkpoints**: May contain traces of training data
- **Logs**: Must be sanitized of PII before sharing
- **Configuration**: Use environment variables, never hardcode
- **Analytics**: Aggregate only, never individual-level

### 🟢 SAFE - Can Be Committed
- **Code**: Source files without embedded secrets
- **Documentation**: Public-facing docs, architecture diagrams
- **Schemas**: Database schemas, API contracts
- **Tests**: Unit tests with mocked data

## Security Checklist

### Before Every Commit
- [ ] Run `git status` - review EVERY file
- [ ] Check for accidental inclusion of:
  - [ ] `.env` files or variants
  - [ ] Database files (`*.db`, `*.sqlite`)
  - [ ] User uploads (`*.pdf`, `*.docx`, media files)
  - [ ] Model files (`*.pt`, `*.pkl`, `*.h5`)
  - [ ] Log files containing user data
- [ ] Verify `.gitignore` is working: `git check-ignore <filename>`
- [ ] For new file types, update `.gitignore` FIRST

### API Security
- [ ] All endpoints implement authentication requirements
- [ ] Rate limiting implemented
- [ ] Input validation implemented on all user data
- [ ] Uses ORM to reduce SQL injection risk
- [ ] Implements output sanitization to reduce XSS risk

### AI/ML Security
- [ ] Ollama configured for optimal performance
- [ ] Implements policies to avoid user data in cloud AI calls
- [ ] Implements secure storage for embeddings
- [ ] Implements model output sanitization
- [ ] Implements prompt injection defense measures

### Data Privacy
- [ ] GDPR compliance measures:
  - [ ] Implements explicit consent mechanisms for data processing
  - [ ] Implements data export functionality
  - [ ] Implements right to deletion functionality
- [ ] FERPA compliance measures:
  - [ ] Implements educational records protection
  - [ ] Implements parent/student access controls
  - [ ] Implements audit trail for access

## Environment Variables

### Required `.env.example` Structure

**Note**: This is a template for local development. Production values should never include localhost references.

```bash
# Database (Development Example)
DATABASE_URL=postgresql://user:password@localhost/ai_study_architect
REDIS_URL=redis://localhost:6379

# Authentication (Generate secure values for production)
JWT_SECRET=generate-a-secure-random-string
SESSION_SECRET=another-secure-random-string

# AI Services (Replace with actual keys)
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Storage
UPLOAD_PATH=/secure/location/uploads
MAX_UPLOAD_SIZE=10485760

# Security (Production should use actual domains)
ENCRYPTION_KEY=generate-using-secrets-module
ALLOWED_ORIGINS=http://localhost:5173  # Dev only - use https://aistudyarchitect.com in production
```

## Incident Response

If sensitive data is accidentally committed:

1. **IMMEDIATELY**:
   ```bash
   git reset --hard HEAD~1  # If not pushed
   ```

2. **If Already Pushed**:
   - Contact repository admin immediately
   - Use `git filter-branch` or BFG Repo-Cleaner
   - Rotate ALL exposed credentials
   - Document incident

3. **Prevention**:
   - Use pre-commit hooks
   - Regular security audits
   - Team security training

## Development Practices

### Local Development
- Use `.env.local` for personal settings
- Never use production data in development
- Generate synthetic test data
- Use Docker volumes for databases

### Code Reviews
- Security-focused review checklist
- Check for hardcoded secrets
- Verify error messages don't leak info
- Ensure logging is appropriate

### Dependencies
- Regular dependency audits: `npm audit`, `pip-audit`
- Keep dependencies updated
- Review new dependencies for security
- Use lock files for reproducibility

## Compliance Requirements

### Data Retention
- Student data: Follows institutional policy
- Logs: Implements 90 days maximum retention
- Backups: Implements encryption at rest
- Deletion: Implements secure wiping procedures

### Access Control
- Implements role-based permissions (Student, Teacher, Admin)
- Implements principle of least privilege
- Implements regular access review procedures
- Implements multi-factor authentication for admins

### Audit Trail
- Implements logging for all data access
- Implements tracking for model interactions
- Implements API usage monitoring
- Implements regular security audit procedures

## Emergency Contacts

- Security Team: security@your-institution.edu
- Data Protection Officer: dpo@your-institution.edu
- Incident Response: incident-response@your-institution.edu

---

Remember: When in doubt, keep it out (of git)!