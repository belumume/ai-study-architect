---
status: pending
priority: p2
issue_id: "016"
tags: [security, pre-existing, backup]
dependencies: []
---

# Remove DATABASE_URL from psql CLI arguments

## Problem Statement

`backend/app/api/v1/endpoints/backup.py:296` passes `DATABASE_URL` directly as a CLI argument to `psql`. This exposes database credentials (including password) in the process list (`ps aux`).

## Proposed Solution

Parse the URL and use `PGPASSWORD` environment variable instead:
```python
env={**os.environ, "PGPASSWORD": parsed_password}
```
Or use `.pgpass` file.

## Acceptance Criteria

- [ ] Database credentials not visible in process list
- [ ] Debug endpoint still functional behind BACKUP_TOKEN
