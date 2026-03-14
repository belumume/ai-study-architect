---
event: Stop
enabled: true
---

# Test Coverage Check Before Completion

Before declaring work complete, verify:

1. If backend Python files were modified this session, were backend tests run? Check for pytest output in conversation history.
2. If frontend TypeScript files were modified, were frontend tests run? Check for vitest/npm test output.
3. If new features were added (new endpoints, new components, new services), were tests written for them?

If any of these checks fail, remind: "Tests not verified. Run `pytest tests/ -v` (backend) and/or `npm test` (frontend) before claiming done."

Do NOT block — just remind. The user can choose to proceed.
