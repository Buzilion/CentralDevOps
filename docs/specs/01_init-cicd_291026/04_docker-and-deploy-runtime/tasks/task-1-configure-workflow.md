# Task 1: Configure workflow and preflight

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Spec 03 checklist complete; spec 02 dispatch proof identifies the App actor; spec 01 workflow lint/name checker available |
| Needs | CentralDevOps code-owner review; no VPS credentials are needed to implement local preflight tests |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Create the on-demand `configure-vps.yml` workflow with least privilege and make invalid callers/inputs fail before any host connection or secret-bearing work.

## Relevant files or references

- Create `.github/workflows/configure-vps.yml`
- Create `deployment/tools/validate-configure-inputs.py` and focused tests
- `docs/design/variables-and-secrets.md` §§1, 3.1–3.2
- Spec sections: Configure workflow contract, Error Behavior
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` for the verified dispatch App actor ID

## Proposed approach

1. Require the completed spec 03 checklist and the spec 02 actor identity evidence before implementation. Do not guess the actor ID.
2. Add only `workflow_dispatch` inputs: exact Environment and profile choices, optional single limit, and a `check_mode` boolean defaulting to `true`.
3. Set `permissions: {}` at workflow scope. Grant only `contents: read` where checkout is needed; pin third-party actions to reviewed full commit SHAs and disable persisted checkout credentials.
4. Gate the privileged job on a caller actor ID different from the proven dispatch App ID and a workflow ref allowed by the selected Environment: any branch for `Staging`, and `release/*` for `Production`. Associate the job with the exact selected GitHub Environment so Production approval precedes credential use.
5. Pass workflow inputs through environment variables; never interpolate `${{ inputs.* }}` or event fields directly into shell.
6. Preflight the selected inventory and exact host/group limit before invoking Ansible. Prevent arbitrary Ansible limit syntax or CLI argument injection.
7. Use `ANSIBLE_SSH_PRIVATE_KEY` for admin access and `GHCR_PULL_TOKEN` for host provisioning. Do not reference `DEPLOY_SSH_PRIVATE_KEY` from this workflow.
8. Run the workflow lint and naming checker; catalog any new names in the same change.

## Acceptance criteria

- Workflow is manual-only, least-privilege, pinned, and has no direct shell interpolation of untrusted values.
- A ref not allowed by the selected Environment and the dispatch App actor cannot start the privileged Environment-bound job.
- Invalid choices, malformed/unknown limits and cross-Environment limits fail before SSH.
- The inventory path is derived from `target_environment`, never accepted as an input.
- Tests cover each rejection and demonstrate no Ansible/SSH invocation on invalid requests.
- `check_mode` defaults to dry run and uses `--check --diff`; convergence requires an explicit input.

## Source reference

INF-05, INF-08, INF-14, INF-15; SEC-14; D-01 to D-03, D-13.

## Verify

- Run the repository's `workflow-lint` and `naming-and-secrets` checks.
- Run `python -m unittest discover -s deployment/tools/tests`.
- Inspect the workflow job condition and Environment binding; test all negative preflight cases locally.

## Out of scope

Running Ansible against any host, creating secrets, or implementing Docker/runtime roles.
