# Session 16: Dependabot security pass, deploy regression, todos 050/051

Date: 2026-05-31

## Summary

Cleared all 66 open Dependabot alerts (1 critical, 28 high, 34 medium, 3 low) to 0, resolved the two open follow-up todos (050, 051), and root-fixed a deploy regression introduced mid-pass. Production verified live end-to-end (including the full JWT lifecycle under the new cryptography).

## What shipped (PRs, in order)

| PR | Change | Notes |
|----|--------|-------|
| #64 | npm safe fixes (`npm audit fix`, no `--force`) | frontend 29->11, worker 4->0; all runtime npm advisories cleared |
| #65 | backend safe pip bumps | python-jose 3.3->3.4 (CRITICAL JWT algo confusion), python-multipart 0.0.6->0.0.27, cryptography 42.0.2->42.0.4, Pillow 10.2->10.3, requests 2.31->2.33, python-dotenv 1.0->1.2.2 |
| #66 | revert worker wrangler 4.95->4.73.0 | unblock the broken deploy (see below) |
| #67 | todos 050 (P1) + 051 (P2) + 11 tests | context-override security fix + HTTPException propagation |
| #68 | Pillow 12.2.0 + cryptography 46.0.6 (MAJOR) | cleared the remaining runtime highs |
| #69 | PyPDF2 -> pypdf | the only no-patch advisory; deprecated package migration |
| #70 | pin wrangler 4.73.0 exact | durable guard for the Node-20 deploy |
| #71 | @typescript-eslint 6->8 + vitest 1->4 | dev tooling; cleared minimatch/esbuild/vite (dev-scope) |
| #74 | pytest 7->9 (+pytest-asyncio 1.3.0, pytest-cov 6.0.0) | dev tooling |
| #75 | CI to Node 22 + wrangler 4.95.0 | cleared the worker undici advisories; superseded #70's pin |

## The deploy regression (root cause + fix)

`npm audit fix` in `worker/` (PR #64) bumped `wrangler` 4.73.0 -> 4.95.0 to fix a transitive `undici` advisory. wrangler 4.94+ requires Node >= 22, but `deploy.yml` ran Node 20, so `npx wrangler deploy` failed with "Wrangler requires at least Node.js v22.0.0" and blocked the production deploy of #64 AND #65. The local machine (Node 24) installed it cleanly, masking the issue until CI.

Two-stage fix:
1. #66 reverted the worker lockfile to wrangler 4.73.0 (immediate unblock).
2. #70 pinned wrangler exactly (the revert alone was not durable: `worker/package.json` still had `"wrangler": "^4"`, so the next `npm install` would re-resolve the caret and re-break).
3. #75 then bumped CI to Node 22 and wrangler to 4.95.0, which is the proper long-term fix (current LTS, wrangler current, undici cleared).

Lesson: after audit-fixing a build/deploy tool, check the resolved version's `engines.node` against the CI runner's Node version. Pin deploy-critical tools exactly, or align the CI Node version. A reverted lockfile is not durable while the manifest keeps a caret.

## The Pillow advisory-range trap

Pillow 10.2.0 had a HIGH `< 10.3.0` advisory. Bumping to 10.3.0 (PR #65) cleared it but EXPOSED 3 other advisories with ranges `>= 10.3.0, < 12.2.0` (PSD-tile OOB, FITS GZIP bomb, OOB write) that only apply to >= 10.3.0. Net: 10.3.0 traded one high for three; only 12.2.0 (PR #68) cleared them all.

Lesson: for a package with multiple open advisories, target the version that clears the union of all advisory ranges, and re-pull the alerts after bumping to confirm none were newly exposed.

## Verification

- Empirical: each major bump tested in an isolated Python 3.12 venv (matching the prod `python:3.12-slim`) against the app's exact usage (Pillow open/new/thumbnail, RSA keygen via default_backend, Fernet, jose RS256). pytest 9 verified by collecting all 520 tests under pytest-asyncio 1.3.0 (asyncio_mode=auto).
- CI: full backend pytest (with the Postgres service) + frontend vitest + build green on every PR.
- Live (post-deploy): authenticated flow confirmed end-to-end under cryptography 46.0.6 (auth/me, dashboard, and a full auth/me 401 -> refresh -> auth/me 200 rotation cycle all 200).

## todos 050 / 051

- 050 (P1 security): `/agents/*` spread `request.context` into the agent input dict AFTER the trusted `user_id`/`action`/`user_input`, letting a client override the authenticated user. Fixed by spreading context FIRST. Only `agent_chat` had the pattern; a sibling-endpoint scan found no others.
- 051 (P2): added `except HTTPException: raise` before the broad `except Exception` in the 6 agent endpoints + `backup.trigger_backup`, so 404/400/429 propagate instead of being masked as 500. Covered by 11 new tests in `tests/test_agents_api.py`.

## Related
- `docs/solutions/integration-issues/session15-todo-resolution-search-cache-auth-lint-compound.md`
- Global rule: dependency-bump security gotchas (Node engine mismatch, advisory-range exposure, surgical methodology)
