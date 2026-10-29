# Task 6: Runtime acceptance and runbook

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Tasks 1–5; spec 03 disposable-host hardening proof |
| Needs | Disposable VPS only; Staging credentials; no production workload or secret |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Prove the delivered configure/runtime behavior safely on a disposable VPS and document safe operation and audit procedures.

## Relevant files or references

- Create `docs/runbooks/configure-vps.md`
- Create a sanitized task summary under `summaries/` when this task closes
- INF-03, INF-04, INF-05, INF-11, INF-12; SEC-06, SEC-11

## Proposed approach

1. Run check mode for the delivered Docker and deploy-runtime roles and compare host state before/after; confirm no change.
2. Exercise the delivered roles on the disposable host; verify Docker/Compose, `edge` and `db`, deploy account restrictions, sudo scope, and root-only token storage.
3. Run those roles again unchanged and record zero changes. Also test that configure preflight rejects a profile with an undelivered role before any SSH connection.
4. Exercise invalid Environment, cross-inventory limit, overlapping subnet, entrypoint invocation, arbitrary sudo, Docker access, and token read/write denial. Confirm each fails closed.
5. Write the runbook with exact workflow inputs, dry-run and normal operation procedures, verification commands, required approvals, failure handling and credential-safe diagnostics.
6. Record sanitized evidence (date, host alias, tested roles/profile, run URLs/commit, changed counts, checks and outcomes). Do not include tokens, keys, IPs marked sensitive by the operator, or runtime data.
7. If every role in a profile is available, run the full profile in check mode and normal mode, then confirm a second unchanged run reports zero changes. Otherwise record that full-profile proof is deferred; do not add placeholder roles or claim a partial run as complete.

## Acceptance criteria

- The delivered Docker and deploy-runtime roles pass acceptance on the disposable VPS, with no Production host or real application workload used.
- Configure preflight rejects a profile with a missing role before any host connection.
- No test changed a Production host or exposed any credential.
- The runbook explains that later-spec roles must exist before a profile can execute and that deploy entrypoints remain disabled until spec 11.
- Any profile not fully testable because later roles are missing is clearly recorded as deferred; no full-profile success is claimed.
- Evidence is sanitized and the task summary/checklist are updated according to the repository's task-closing convention.

## Source reference

INF-03, INF-04, INF-05, INF-11, INF-12, INF-13; SEC-06, SEC-11, SEC-12.

## Verify

- Review the sanitized evidence against each invariant in the spec.
- Run the repository workflow lint, name checker, and focused unit tests.
- Re-run the delivered roles unchanged and confirm zero changes; if a profile is complete, also confirm the full-profile second run is unchanged.

## Out of scope

Applying this configuration to Staging or Production VPSs, deploying an application, or checking off tasks whose acceptance criteria are not evidenced.
