# Task 1: Define the deploy workflow boundary

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/10_deploy-authorization/spec.md` |
| Depends on | None within this spec; the spec-level prerequisites still apply |
| Summary | `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-1-summary.md` (write when the task closes) |

## Goal

Create the reviewed CentralDevOps workflow contract without giving the authorization job Environment secrets or deployment capability.

## Relevant files or references

- `.github/workflows/deploy-app.yml`
- `deployment/config/deploy-dispatch-app.json`
- `deployment/tools/github-names.json`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/`
- `docs/design/variables-and-secrets.md` §§2, 4.4, 6
- `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` (source-run correlation inputs)

## Proposed approach

1. Add only the dispatch inputs `target_environment`, `image_ref`, `oidc_token`, `sealed_bundle`, `source_run_id` and `source_run_attempt`. The last two are strings used only for correlation and must later match the signed claims.
2. Record the decimal `github.actor_id` observed in the successful spec 02 proof in non-secret reviewed configuration. Do not infer it from a caller input or guess a bot login.
3. Set top-level `permissions: {}`; give each job explicit read-only permissions. Pin every action and disable persisted checkout credentials.
4. Add a no-permission `reject-disallowed-environment-ref` job so a CentralDevOps ref not permitted by the requested Environment fails before checkout or Environment selection (`Staging`: any branch; `Production`: `release/*` only). Verify the trusted event actor separately from OIDC.
5. Establish the `derive-request-key`, `authorize` and Environment-bound `deploy` job boundary. The last job is preflight-only in spec 10; spec 11 extends it with execution rather than adding a second Environment job.
6. Add `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` to the existing GitHub name catalog as an Environment secret introduced by this spec. Do not reference the admin key, provider password or Vault password.

## Acceptance criteria

- The workflow has exactly six dispatch inputs and no caller-supplied app identity.
- Correlation inputs are not treated as authorization and have to match signed OIDC claims.
- A non-main Staging dispatch is accepted; a Production dispatch outside `release/*` ends in failure without checkout or an Environment-bound job. The App actor check uses trusted GitHub context.
- The `authorize` job has no `environment`, no repo/org/Environment secrets, and no write permission.
- The `deploy` job can select only a validated authorization output; it performs no SSH or host operation in this task.
- The secret catalog and workflow lint accept the new workflow, and no forbidden admin secret appears in it.

## Source reference

DEP-01, DEP-16, SEC-10, SEC-14; spec 12 D5; requirements A-01 to A-04.

## Verify

- Run actionlint and zizmor on the workflow; run the repository naming/secrets check.
- Inspect the job graph and permissions for non-main Staging, Production `release/*`, and disallowed Production-ref dispatch cases.
- Confirm `deployment/config/deploy-dispatch-app.json` contains only the non-secret decimal actor ID established by spec 02.

## Out of scope

OIDC verification, registry lookups, bundle decryption, SSH deployment or app-side dispatch implementation.
