---
status: pending
priority: p2
issue_id: "051"
tags: [code-review, quality]
---

## Problem Statement

In `backend/app/api/v1/agents.py:283`, an `HTTPException(404)` for missing agents is raised inside a `try` block, but the surrounding `except Exception` catches it and re-wraps it as a 500 error. Missing agents return the wrong status code.

Identified by cubic (PR #56 review).

## Proposed Solution

Catch `HTTPException` separately and re-raise, or restructure the try/except:
```python
except HTTPException:
    raise  # Let FastAPI handle it
except Exception as e:
    raise HTTPException(status_code=500, ...) from e
```

## Files Affected

- `backend/app/api/v1/agents.py` (line ~283)

## Effort Estimate

Small
