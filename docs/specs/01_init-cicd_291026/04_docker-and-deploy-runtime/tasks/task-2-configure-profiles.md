# Task 2: Configure playbook, profiles and dry run

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Task 1; spec 03's Ansible configuration and baseline roles |
| Needs | Pinned Ansible and collections established by spec 03 |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Implement the configure playbook and profile contract without allowing a partial or cross-Environment run.

## Relevant files or references

- Create/update `playbooks/configure.yml`
- Update `.github/workflows/configure-vps.yml` only for the tested playbook invocation
- `docs/design/naming-and-repository-conventions.md` §7
- v5 design §6.2; spec sections: Configure profiles, Configure workflow contract

## Proposed approach

1. Implement the exact role sets in the spec as a single reviewed profile map; deduplicate shared roles for `all-in-one`.
2. Before any remote task, assert every role selected by the profile exists. A missing later-spec role is a hard preflight failure, never a skipped include.
3. Resolve the inventory from the selected Environment only. Accept an optional exact inventory alias or group already validated by Task 1; otherwise target the selected inventory's full target set.
4. Invoke Ansible check mode and diff only when `check_mode=true`. Ensure role tasks use check-mode-aware Ansible modules and never bypass check mode with mutating shell commands.
5. Prove the delivered roles' check-mode and idempotence behavior with focused tests. Do not claim a full-profile result while that profile includes a role not yet delivered.

## Acceptance criteria

- Tests assert exact membership and ordering for all five profiles and de-duplicated all-in-one behavior.
- Missing roles and missing required inventory values fail before SSH with a clear error.
- Dry run uses `--check --diff`; tests show the delivered roles do not mutate state in check mode.
- A complete profile is run twice on an unchanged disposable host when all its roles are available; the second run reports zero changes. If later roles are still missing, the evidence explicitly records that full-profile acceptance is deferred and the profile preflight rejects the request.
- No workflow accepts an inventory path or arbitrary Ansible arguments from an operator.

## Source reference

INF-03, INF-04, INF-05, INF-08; D-02 to D-05.

## Verify

- Run profile-map and preflight unit tests.
- Inspect the Ansible command line for a fixed playbook and inventory; only a prevalidated exact limit can be passed.
- Verify check-mode behavior on the disposable host before considering a complete profile ready for service hosts.

## Out of scope

Implementing roles owned by later roadmap specs (Nginx, Certbot, PostgreSQL, backup or collector).
