# Task 4: Restricted deploy runtime

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Task 3; spec 03's users and SSH baseline |
| Needs | Dedicated test deploy key pair; disposable VPS only |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Provision the deploy identity and its fail-closed server-side entrypoints without granting Docker or general root access.

## Relevant files or references

- Create/update `roles/deploy_runtime/`
- Create `deployment/scripts/centraldevops-deploy`
- Create `deployment/scripts/centraldevops-route`
- `docs/design/variables-and-secrets.md` §4.3
- v5 design §8.5; spec sections: Restricted deploy runtime, Invariants

## Proposed approach

1. Reuse the `cdo-deploy` account created by spec 03; verify it is unprivileged and has no `docker`, admin, or other privileged group membership. Fail if the expected account is absent.
2. Install only the matching Environment's deploy public key with SSH `restrict`; do not place a private key on the host.
3. Install root-owned, deploy-unwritable scripts at the two fixed paths. In this spec, every invocation is fail-closed and returns nonzero without changing state; spec 11 defines the accepted argument contract and replaces the stubs.
4. Add a sudoers rule naming only the two absolute script paths, without an interactive password. Keep all parsing/validation in the root-owned scripts; allow no root shell, Docker command, or general sudo command.
5. Enable session and sudo auditing without logging input file contents or secrets.

## Acceptance criteria

- `cdo-deploy` can authenticate only with its dedicated matching Environment key and has no Docker/socket access.
- The account cannot modify either entrypoint, sudoers file, or other root-owned runtime data.
- `sudo -l -U cdo-deploy` shows only the two allowed entrypoints.
- A root shell through sudo, direct Docker access, unrelated sudo commands, and all pre-spec-11 entrypoint invocations fail without side effects.
- A Staging deploy key cannot authenticate to the Production host and vice versa.

## Source reference

INF-12, INF-13; SEC-06; D-08, D-09.

## Verify

- Test permitted and denied sudo commands on the disposable VPS.
- Check ownership/modes and test direct Docker invocation as `cdo-deploy`.
- Review SSH/sudo logs for attribution and confirm no sensitive values are recorded.

## Out of scope

Deployment behavior, Compose policy, rollback, health checks, or route changes (specs 06, 10 and 11).
