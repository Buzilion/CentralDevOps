# Task 5: Deploy-runtime integrity checks

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` |
| Depends on | Tasks 1–4; spec 04 deploy-runtime role is implemented |
| Needs | Disposable VPS with the spec-04 deploy runtime configured |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Verify the restricted deploy account, root-owned entrypoints, their integrity, and the narrow sudo boundary without reading or exposing credentials.

## Relevant files or references

- Add a read-only check to `roles/deploy_runtime/tasks/verify.yml`
- Reviewed sources: `deployment/scripts/centraldevops-deploy` and `deployment/scripts/centraldevops-route`
- `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md`
- Spec 05 check matrix and result contract

## Proposed approach

1. Confirm `cdo-deploy` exists, is not in the Docker or privileged groups, and cannot use Docker directly.
2. Check both installed entrypoints exist, are root-owned, are not writable by the deploy account, and have checksums matching their reviewed repository source.
3. Validate sudoers syntax and verify `cdo-deploy` may run only the two approved absolute script paths; reject broad or extra privileges.
4. If the GHCR token file is part of the installed role, inspect only its owner/group/mode. Never read its content or include it in output.
5. Add negative fixtures for a changed script, deploy-writable file, extra sudo permission, Docker membership, and incorrect token-file mode.
6. Keep failure details sanitized and avoid reporting script contents, credential paths' contents, or private values.

## Acceptance criteria

- The deploy account has no Docker-equivalent privilege and no unapproved sudo capability.
- Both server-side scripts are present, root-owned, non-deploy-writable, executable as required, and checksum-verified against the repository.
- Sudoers syntax is valid and the effective allowed command set contains only the two approved entrypoints.
- Token-file verification, when applicable, checks metadata only and never reads the token.
- Each injected integrity or privilege failure is reported and fails the overall verification run.

## Source reference

INF-06, INF-12, INF-13; SEC-06, SEC-11, SEC-12; HV-04 to HV-07.

## Verify

- Run focused tests and Ansible syntax/lint.
- On the disposable VPS, alter a test entrypoint, verify that the checksum check fails, then restore it from the reviewed source and confirm the check passes.
- Confirm no token or script content appears in task output or workflow logs.

## Out of scope

Changing sudoers, repairing scripts, rotating keys/tokens, or implementing deploy/route behavior.
