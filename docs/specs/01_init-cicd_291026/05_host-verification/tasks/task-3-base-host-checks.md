# Task 3: Base host and firewall checks

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` |
| Depends on | Tasks 1–2; spec 03 host roles and inventory are implemented |
| Needs | Disposable VPS for host-level acceptance; no Staging/Production service host |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Add read-only verification for the bootstrap/security roles: admin access, expected accounts, SSH hardening, firewall state, automatic security updates, and disk/inode measurements.

## Relevant files or references

- Add checks to `roles/common/tasks/verify.yml`, `roles/users/tasks/verify.yml`, `roles/ssh_hardening/tasks/verify.yml`, and `roles/firewall/tasks/verify.yml` as applicable
- `inventories/<environment>/hosts.yml` and `inventories/<environment>/known_hosts`
- `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md`
- Spec 05 check matrix and read-only result contract

## Proposed approach

1. Confirm each check runs only for the role assigned by the selected inventory/profile and is included by `playbooks/verify.yml`.
2. Verify an admin-key SSH connection through the pinned host key, existence of `cdo-admin` and `cdo-deploy`, and the effective SSH policy for root/password/keyboard-interactive access.
3. Verify the firewall is active and its effective ingress matches the host's declared SSH policy and allowed web ports; reject public database, app, or Docker API access.
4. Verify automatic security updates are enabled without changing package state.
5. Report used/available disk space and inode use for the required filesystems. Fail when required measurements cannot be read; do not invent a numeric pressure threshold.
6. Ensure output reports status and sanitized details only, never inventory secrets or credentials.

## Acceptance criteria

- Every base check has a unique ID, one result per selected host, and a failure fixture.
- SSH hardening is verified from effective configuration, not only from a source file.
- Expected accounts, active firewall policy, automatic updates, and disk/inode measurements are checked without mutation.
- The verifier fails on unexpected public ingress or unavailable required data.
- Successful disposable-host verification leaves persistent host state unchanged.

## Source reference

INF-06, INF-09, INF-10; HV-04 to HV-07.

## Verify

- Run focused tests for valid and invalid SSH, account, firewall, update, and filesystem states.
- Inspect a disposable-host run and compare relevant persistent state before and after.
- Confirm each check's failure appears in the final report and causes a nonzero run result.

## Out of scope

Docker/network checks, deploy-runtime integrity, and any remediation of a host.
