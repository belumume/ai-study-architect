---
status: pending
priority: p2
issue_id: "027"
tags: [api, production, content, bug]
dependencies: []
---

# Content search returns 500 on production

## Problem Statement

`GET /api/v1/content/search?q=test` returns 500 (Internal Server Error) on production with valid auth token. The route ordering fix (todo 022, moved before /{content_id}) resolved the 422 but the endpoint itself crashes on Neon.

## Likely Cause

The search endpoint uses `func.lower()` and `.like()` on Content columns. Possible issues:
- `func.case()` for relevance scoring may generate incompatible SQL
- NULL columns combined with OR/LIKE may produce unexpected query behavior
- Collation or locale differences between local PG and Neon
- Check generated SQL via SQLAlchemy echo or Neon query logs

## Reproduction

```bash
TOKEN=$(curl -s -X POST https://aistudyarchitect.com/api/v1/auth/login ...)
curl -s "https://aistudyarchitect.com/api/v1/content/search?q=test" -H "Authorization: Bearer $TOKEN"
# Returns: Internal Server Error (500)
```

## Acceptance Criteria

- [ ] Search returns 200 with results or empty array on production
- [ ] No 500 errors in production logs for search endpoint
