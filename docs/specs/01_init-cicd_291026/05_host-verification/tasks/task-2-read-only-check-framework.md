# Task 2: Read-only verification framework

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` |
| Depends on | Task 1 |
| Needs | Local Ansible and focused test environment |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Create the Ansible verification entrypoint and a consistent result contract that reports every applicable check while keeping the overall run fail-closed and read-only.

## Relevant files or references

- Create `playbooks/verify.yml`
- Create or extend the shared verification tasks/helper used by `roles/<role>/tasks/verify.yml`
- Spec 05 sections: Read-only execution and result contract, Invariants
- `docs/design/infrastructure-contracts-and-invariants.md` §5

## Proposed approach

1. Use the inventory and target resolved by Task 1 and the selected Environment's strict host-key settings.
2. Define stable check IDs and emit exactly one sanitized `PASS` or `FAIL` line per applicable check and host.
3. Collect independent check outcomes so one failure does not hide later results. Fail the host/workflow after reporting all applicable checks if any outcome is failed or indeterminate.
4. Treat an unreachable host as failed; report every applicable check that could not run as `FAIL`, not as a pass or silent skip.
5. Use read-only modules/commands only. Mark read commands unchanged, avoid shell interpolation, clean temporary Ansible module files, and do not rely on `--check` to make mutating tasks safe.
6. Keep secret-bearing operations out of the verifier. Sanitize command details and never print tokens, private keys, raw environment files, or unfiltered output.
7. Add tests for result uniqueness, applicability, aggregation, unreachable hosts, and malformed/unavailable check data.

## Acceptance criteria

- `playbooks/verify.yml` passes syntax and lint checks and targets only the validated selected inventory/scope.
- Every applicable host/check pair has one result with a stable ID and sanitized detail.
- Any failed or indeterminate check produces a nonzero overall result after independent checks have reported.
- An unreachable host and checks that cannot be evaluated never produce success-shaped output.
- Verification tasks do not change persistent host state; temporary Ansible data is cleaned up.
- Tests prove failures are aggregated and no secrets or raw sensitive command output are reported.

## Source reference

INF-06; HV-04, HV-05; decisions D1 and D4.

## Verify

- Run `ansible-playbook --syntax-check`, `ansible-lint`, and focused verifier tests.
- Use controlled task results to test pass, failure, unavailable data, and unreachable-host aggregation.
- Review all verifier commands/modules for persistent writes and secret output.

## Out of scope

Implementing individual host, Docker, or deploy-runtime checks; those are Tasks 3–5.
