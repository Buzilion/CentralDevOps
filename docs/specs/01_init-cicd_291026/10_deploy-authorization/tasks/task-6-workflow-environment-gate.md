# Task 6: Integrate authorization and the Environment gate

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/10_deploy-authorization/spec.md` |
| Depends on | Tasks 1–5 |
| Summary | `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-6-summary.md` (write when the task closes) |

## Goal

Connect the verified authorization plan to the one Environment-bound preflight job and preserve a single Production approval boundary for spec 11.

## Relevant files or references

- `.github/workflows/deploy-app.yml`
- `.github/rulesets/main.json` and `docs/runbooks/github-environments.md`
- `deployment/tools/verify-oidc.py`
- `deployment/tools/replay-guard.py`
- `deployment/tools/validate-registry.py`
- `docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/spec.md`
- `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md`

## Proposed approach

1. Wire `authorize` to complete actor, OIDC, correlation, registry, digest, provenance, placement and replay checks before it exposes its allowlisted outputs.
2. Make the single Environment-bound `deploy` job depend on successful authorization and select its Environment only from the validated output; never use the raw request input in the `environment` expression.
3. Keep the Environment-bound job preflight-only in this spec. It may read the age key after approval, but not the SSH key; it cannot contact or change a host.
4. Confirm Staging proceeds without approval and Production waits only after authorization. Once approval is granted, do not re-check OIDC expiry; the authenticated plan is the job input.
5. Emit the sanitized source correlation hash before authorization and the separate replay claim after authorization so spec 12 can locate both rejected and accepted requests through the Actions API.
6. Document the handoff so spec 11 extends this same job after preflight and does not create another Environment-bound job or a second approval wait.
7. Run all repository workflow and secret-name checks, then inspect the final permissions and job graph.

## Acceptance criteria

- Failed authorization never starts an Environment-bound job.
- The only Environment value used by the job is a validated `Staging` or `Production` output.
- Production approval is requested after authorization; authorization completes before the wait.
- The pre-authorization correlation hash is stable and matches the value computed by the spec 12 action from its repository/run context, including for rejected requests.
- The workflow does not reference `DEPLOY_SSH_PRIVATE_KEY` or connect to a host in this spec.
- Spec 11 can add deployment steps to this job without duplicating the approval boundary.

## Source reference

DEP-02, DEP-06, DEP-08, DEP-16; spec 12 D5; requirements A-02, A-04, A-09, A-10 and A-13.

## Verify

- Run actionlint, zizmor and the naming/secrets checker.
- Review a successful synthetic Staging run and a rejected request; verify the job graph and sanitized outputs.
- Confirm a non-main dispatch ends in failure without checkout or Environment selection.
- Confirm a Production run reaches the approval wait only after `authorize` completes. Use a clock-controlled test to show preflight does not revalidate the expired token.

## Out of scope

Production deployment, rollback, host-side locks, health checks, route activation or the Staging live-deploy gate owned by spec 11.
