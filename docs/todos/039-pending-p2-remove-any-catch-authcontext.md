---
status: pending
priority: p2
issue_id: "039"
tags: [code-review, quality]
---

## Problem Statement
`catch (err: any)` in AuthContext login and register blocks defeats TypeScript type checking. Accessing `err.response?.data?.detail` without narrowing is type-unsafe.

## Proposed Solution
Use `unknown` with Axios type guard:
```typescript
import { isAxiosError } from 'axios'

} catch (err: unknown) {
  if (isAxiosError(err)) {
    setError(err.response?.data?.detail || 'Login failed.')
  } else {
    setError('Login failed. Please try again.')
  }
}
```

## Files Affected
- frontend/src/contexts/AuthContext.tsx (lines 69, 84)

## Effort Estimate
Small
