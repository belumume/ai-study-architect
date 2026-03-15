---
title: "Dashboard Vercel URL Crash + Backup S3 Guard + AWS Key Rotation"
date: 2026-03-15
session: 12
type: production_bugfix
status: completed
pr: "#30"
scope: 2 bugs + 1 operational task
tags: [vercel, spa-routing, github-actions, secrets, aws-iam, backup, s3, r2]
files_modified:
  - frontend/src/pages/DashboardPage.tsx
  - .github/workflows/backup.yml
  - docs/ops/BACKUP_SETUP.md
  - CLAUDE.md
root_causes:
  - missing_array_guard_on_api_response
  - github_secrets_in_if_conditional
  - stale_iam_key_219_days
---

# Dashboard Vercel URL Crash + Backup S3 Guard + AWS Key Rotation

## Problem 1: Dashboard Crash on Vercel URL

### Symptom
Visiting `ai-study-architect.vercel.app` showed ErrorBoundary "Oops! Something went wrong" with `TypeError: Cannot read properties of undefined (reading 'length')`.

Production URL (`aistudyarchitect.com`) was unaffected.

### Root Cause
The Vercel URL bypasses the CF Worker — there's no backend proxy. When `DashboardPage` calls `/api/v1/dashboard/`, Vercel's SPA catchall returns `index.html` (HTML) instead of JSON. Axios parses the HTML as a string, so `dashboard` is a truthy string but `dashboard.subjects` is `undefined`. The original code accessed `.length` on `undefined`.

**Architecture issue**: CF Worker routes `/api/*` to the backend container. Hitting Vercel directly skips this routing entirely.

### Solution
Added `Array.isArray(dashboard.subjects)` guard before accessing `.length`:

```typescript
// frontend/src/pages/DashboardPage.tsx (lines 56-60)
if (
  !dashboard ||
  !Array.isArray(dashboard.subjects) ||
  (dashboard.subjects.length === 0 && dashboard.today_minutes === 0)
)
```

The guard catches non-JSON responses and renders the empty state ("Awaiting Telemetry") gracefully.

### Verification
- Playwright screenshot confirmed Vercel URL renders empty state (no crash)
- Production URL continues working correctly (login page renders)

---

## Problem 2: Backup Workflow Failing Every Sunday

### Symptom
GitHub Actions backup runs #193, #194 failed with `AuthorizationHeaderMalformed`. Only Sunday runs failed — daily Mon-Sat runs succeeded.

### Root Cause
Two issues compounded:

1. **Sunday logic**: The "Determine provider" step sets `provider=both` on Sundays (`date +%u = 7`). This triggers the S3 upload step, but `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` GitHub secrets weren't configured.

2. **GitHub Actions limitation**: `secrets.*` cannot be used in `if:` conditionals (documented at docs.github.com). The initial fix used `secrets.AWS_ACCESS_KEY_ID != ''` which doesn't work as expected.

### Solution
Expose secrets as job-level `env:` vars, then check `env.*` in the conditional:

```yaml
# .github/workflows/backup.yml
jobs:
  backup:
    runs-on: ubuntu-latest
    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    steps:
      # ... other steps ...
      - name: Upload to S3
        if: >-
          (steps.provider.outputs.provider == 's3' ||
           steps.provider.outputs.provider == 'both') &&
          env.AWS_ACCESS_KEY_ID != '' &&
          env.AWS_SECRET_ACCESS_KEY != ''
```

Job-level `env:` vars are inherited by all steps, eliminating the need for a redundant step-level `env:` block (CodeRabbit review finding).

### Review Findings Addressed
- **Cubic P1**: `secrets.*` in `if:` conditional replaced with `env.*` per GitHub docs
- **Cubic P3**: Now checks both AWS key and secret (not just key)
- **CodeRabbit**: Job-level env vars use standard AWS names, step-level env block removed

### Verification
- Manual trigger with `provider=both`: run 23113606621 succeeded
- R2 uploaded, S3 skipped gracefully (pre-key rotation)
- After key rotation: both R2 + S3 succeeded

---

## Problem 3: AWS IAM Key Rotation (Operational)

### Context
IAM user `ai-study-architect-user` had a 219-day-old access key (`AKIA...HQTNJ`) that was last used for `servicequotas` (not S3). The key was created during the Render era and never rotated after the Cloudflare migration. GitHub secrets were never set, so S3 backups silently skipped for months.

### Steps Performed
1. **Deactivated + deleted** old key via AWS console (Chrome Extension automation)
2. **Cleaned S3 bucket** — removed 4 Render-era backups (Sep 2025, 259.4 KB)
3. **Created new key** — tagged "GitHub Actions S3 backup"
4. **Set GitHub secrets** — `gh secret set AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
5. **Verified end-to-end** — backup run with `provider=both` succeeded (R2 + S3)

### Documentation Updated
- `docs/ops/BACKUP_SETUP.md` — rewritten for CF Container era (v3.0), removed all Render references
- `CLAUDE.md` — corrected RSA key info (now env vars, not rebuild-on-deploy) + added `utcnow()` note

---

## Prevention Strategies

### 1. Validate API Response Shape, Not Just Truthiness
All API response consumers should check the expected structure before accessing properties. A truthy response doesn't mean valid JSON with the expected schema.

```typescript
// Bad: truthy check only
if (!dashboard || dashboard.subjects.length === 0) { ... }

// Good: shape validation
if (!dashboard || !Array.isArray(dashboard.subjects) || ...) { ... }
```

### 2. GitHub Actions Secrets Pattern
Never use `secrets.*` in `if:` conditionals. Always expose as `env:` vars first:

```yaml
env:
  MY_SECRET: ${{ secrets.MY_SECRET }}
# Then in steps:
if: env.MY_SECRET != ''
```

### 3. IAM Key Hygiene
- Rotate keys every 90 days (AWS best practice)
- Tag keys with their purpose ("GitHub Actions S3 backup")
- After any infrastructure migration, audit which credentials are still needed
- AWS "Last used service" only shows the most recent service — not a history

---

## Related Documentation
- `docs/ops/BACKUP_SETUP.md` — backup infrastructure documentation (updated this session)
- `docs/solutions/integration-issues/session10-security-ci-phase2-monetization-compound.md` — prior session's security hardening
- PR #30: `fix/dashboard-guard-and-backup-s3` — squash-merged to main
- Commit `938350f`: docs update (BACKUP_SETUP.md + CLAUDE.md)

## Cross-References
- GitHub Actions secrets limitation: https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions
- Vercel SPA routing: catchall serves index.html for all paths including /api/*
- CF Worker routing: `/api/*` and `/health*` to container, everything else to Vercel proxy
