---
status: pending
priority: p2
issue_id: "038"
tags: [code-review, quality]
---

## Problem Statement
`_retry` is an untyped property on `AxiosRequestConfig`. Accessing and setting it relies on a loose index signature. If Axios tightens types, this breaks silently.

## Proposed Solution
Add module augmentation:
```typescript
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _retry?: boolean
  }
}
```

## Files Affected
- frontend/src/services/api.ts (lines 88, 92)

## Effort Estimate
Small (one-liner type declaration)
