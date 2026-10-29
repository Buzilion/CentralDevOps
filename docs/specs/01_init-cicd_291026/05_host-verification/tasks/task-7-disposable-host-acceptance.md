# Task 7: Disposable-host verification acceptance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` |
| Depends on | Tasks 1–6 |
| Needs | Disposable VPS configured by specs 03 and 04; never use a Production service host for fault injection |
| Summary | Write `summaries/task-7-summary.md` when this task closes |

## Goal

Prove the workflow and currently delivered role checks on a disposable VPS, retain sanitized evidence, and establish the handoff for later role specs.

## Relevant files or references

- `docs/runbooks/verify-vps.md`
- Spec 05 sections: Invariants, Error behavior, Testing strategy
- `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/checklist.md`
- `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/checklist.md`

## Proposed approach

1. Confirm spec 03 and 04 disposable-host acceptance evidence and all local workflow, inventory, Ansible, lint, and unit tests pass.
2. Exercise one exact host target, one group target if available, and whole-Environment target on the disposable inventory. Confirm invalid and cross-Environment targets stop before SSH.
3. Run successful verification and compare relevant persistent package, service, account, firewall, Docker/network, sudoers, and checked-file state before/after.
4. On the disposable host or a controlled test fixture, exercise failed SSH, incorrect network/subnet, exposed Docker API, modified deploy script, invalid sudoers, and unavailable measurements. Confirm all applicable checks report and the workflow fails.
5. Restore any deliberately altered test state, rerun verification, and confirm the host returns to the expected passing state.
6. Record date, commit/run URL, target alias, check IDs, and sanitized results. Do not record credentials, private keys, token contents, or sensitive host data.
7. Mark future role checks as deferred until specs 07, 08, 13, and 14 deliver their roles; do not claim those checks or complete INF-06 beyond the checks actually implemented.
8. Update this spec checklist only when each task's acceptance criteria and evidence are satisfied.

## Acceptance criteria

- Valid target scopes work and invalid/cross-Environment targets fail before any host connection.
- All currently applicable checks report one result per host/check, and any injected failure fails the workflow.
- A successful verification run makes no persistent host changes.
- The deploy-script tamper test is detected, the test state is restored, and a subsequent run passes.
- Evidence is sanitized, dated, and tied to the reviewed commit and workflow run.
- No Staging/Production service host is used for negative or fault-injection tests.
- The checklist accurately records completed tasks, and no deferred future-role check is represented as complete.

## Source reference

INF-06, INF-14, INF-17, INF-18; HV-01 to HV-08.

## Verify

- Review the disposable-host run and evidence against every current check and invariant.
- Re-run local workflow lint, Ansible syntax/lint, and focused unit tests after any acceptance fix.
- Re-run verification after restoring test-only host state.

## Out of scope

Applying configuration changes to a service host, repairing Production, or claiming acceptance for roles owned by later specs.
