# Task 6: Runtime acceptance and runbook

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Tasks 1–5; spec 03 disposable-host hardening proof |
| Needs | Disposable VPS only; Staging credentials; no production workload or secret |

## Goal

Prove configure behavior end to end on the disposable VPS and document safe operation and audit procedures.

## Relevant files or references

- Create `docs/runbooks/configure-vps.md`
- Create a sanitized task summary under `summaries/` when this task closes
- INF-03, INF-04, INF-05, INF-11, INF-12; SEC-06, SEC-11

## Proposed approach

1. Run check mode and compare host state before/after; confirm no change.
2. Run the supported profile on the disposable host; verify Docker/Compose, `edge` and `db`, deploy account restrictions, sudo scope, and root-only token storage.
3. Run configure again unchanged and record zero changes.
4. Exercise invalid Environment, cross-inventory limit, overlapping subnet, invalid deploy arguments, arbitrary sudo, Docker access, and token read/write denial. Confirm each fails closed.
5. Write the runbook with exact workflow inputs, dry-run and normal operation procedures, verification commands, required approvals, failure handling and credential-safe diagnostics.
6. Record sanitized evidence (date, host alias, tested profile, run URLs/commit, changed counts, checks and outcomes). Do not include tokens, keys, IPs marked sensitive by the operator, or runtime data.

## Acceptance criteria

- All acceptance tests in the spec pass on the disposable VPS.
- No test changed a Production host or exposed any credential.
- Runbook clearly explains that later-spec roles must exist before a profile can execute and that deploy entrypoints remain disabled until spec 11.
- Evidence is sanitized and the task summary/checklist are updated according to the repository's task-closing convention.

## Source reference

INF-03, INF-04, INF-05, INF-11, INF-12, INF-13; SEC-06, SEC-11, SEC-12.

## Verify

- Review the sanitized evidence against each invariant in the spec.
- Run the repository workflow lint, name checker, and focused unit tests.
- Re-run configure unchanged and confirm zero changes.

## Out of scope

Applying this configuration to Staging or Production VPSs, deploying an application, or checking off tasks whose acceptance criteria are not evidenced.
