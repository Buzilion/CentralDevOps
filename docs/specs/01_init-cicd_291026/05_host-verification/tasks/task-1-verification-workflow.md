# Task 1: Verification workflow and target preflight

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` |
| Depends on | Spec 04 checklist complete; spec 02 dispatch App identity proven; spec 01 workflow lint and name checker available |
| Needs | No VPS credential is needed for local target-validation tests |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Create the manual `verify-vps.yml` workflow and reject invalid callers or targets before any Environment credential or SSH connection is available.

## Relevant files or references

- Create `.github/workflows/verify-vps.yml`
- Reuse or extract the inventory/target resolver delivered by spec 04; keep its configure behavior and tests intact
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` for the proven App actor ID
- Spec 05 sections: Workflow contract, Error behavior
- `docs/design/variables-and-secrets.md` §4.1

## Proposed approach

1. Confirm all spec-04 checklist items and disposable-host evidence are complete. Obtain the dispatch App actor ID from spec 02; do not guess or use a placeholder.
2. Define only `workflow_dispatch` inputs: required `target_environment` (`Staging` or `Production`) and optional `limit`.
3. Use a secret-free preflight to require `refs/heads/main`, reject the App actor, map the exact Environment to its fixed inventory, and validate an optional exact host/group. Empty `limit` targets every host in that inventory.
4. Reject malformed, unknown, empty-inventory, or cross-Environment targets before the Environment-bound job. Never accept an inventory path, Ansible pattern, extra CLI argument, host address, or credential as input.
5. Pass dispatch values through environment variables. Use least-privilege permissions, pinned actions, and `persist-credentials: false`.
6. Bind the verification job to the selected Environment; use only `ANSIBLE_SSH_PRIVATE_KEY` and strict host-key checking. Confirm any configured `ANSIBLE_INVENTORY_PATH` matches the fixed mapping.
7. Do not add a dry-run switch. Verification must be read-only for every run.

## Acceptance criteria

- The workflow is manual-only and rejects non-`main` refs and the dispatch App actor before the credential-using job.
- Only `Staging` and `Production` are accepted, and the selected Environment determines the inventory and credentials.
- Empty target means the complete selected inventory; a non-empty target exactly matches one host or group in it.
- Unknown, malformed, cross-Environment, and empty-inventory cases fail before Ansible/SSH or secret use.
- Inputs are not interpolated into shell, and no operator-controlled inventory path or Ansible option is accepted.
- The job uses only the admin key, is Environment-bound, and has the required Production protection.
- The resolver's tests cover valid and rejected cases without requiring a live VPS.

## Source reference

INF-06, INF-08, INF-09, INF-14, INF-15; SEC-07, SEC-14; HV-01 to HV-03.

## Verify

- Run workflow lint, naming/secrets checks, and focused resolver tests.
- Inspect the job condition, Environment binding, permissions, action pins, and shell input handling.
- Assert rejected targets never invoke Ansible or SSH.

## Out of scope

Running verification against a VPS or implementing Ansible role checks.
