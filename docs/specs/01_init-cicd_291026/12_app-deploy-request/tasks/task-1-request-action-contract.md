# Task 1: Shared request action contract

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` |
| Depends on | Spec-level gate: specs 10 and 11 checklists complete; continue in roadmap order |
| Needs | A CentralDevOps ref permitted by the requested Environment; reviewed action and workflow lint conventions |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Define the stable, least-privilege interface for the CentralDevOps `request-deploy` action and reject invalid requests before any token or dispatch operation.

## Relevant files or references

- Create `.github/actions/request-deploy/action.yml`
- Add focused action input tests alongside the action
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-05, REL-09, REL-11)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-08, SEC-09, SEC-14)
- `docs/design/naming-and-repository-conventions.md` §6
- Spec 02 `dispatch-trust-proof/spec.md` for the request identity contract

## Proposed approach

1. Define the action at the canonical path `.github/actions/request-deploy/action.yml`. Keep the central repository, target workflow, Environment-to-ref selection, and recipient lookup in reviewed action code rather than caller-configurable inputs. Select a concrete Staging-allowed ref for `Staging` and a concrete branch matching `release/*` for `Production`; do not send the wildcard itself as the dispatch ref.
2. Define required inputs for `target_environment`, `image_ref`, `runtime_env_file`, `compose_file`, `manifest_file`, `dispatch_app_id`, and `dispatch_app_private_key`. Use the caller's GitHub run context for source identity and correlation; do not accept `app_name`, repository identity, host, rollback mode, arbitrary age recipient, or a CentralDevOps ref.
3. Define only sanitized outputs: `central_run_url` and `central_run_result`. Never expose the OIDC token, App installation token, bundle bytes, or runtime values as action outputs.
4. Validate that the Environment is exactly `Staging` or `Production` and that the image reference is a full digest reference before reading or transmitting any sensitive material. Do not interpolate untrusted inputs directly into shell commands. CentralDevOps remains authoritative for registry ownership and policy.
5. Document that callers require only `contents: read` and `id-token: write`, and that app workflows must pin this action to a reviewed full commit SHA.
6. Add tests proving invalid values fail before any API call and error messages identify the invalid field without echoing secret input.

## Acceptance criteria

- The action exists at the canonical path with a documented, required input/output contract.
- `target_environment` rejects all values other than the exact two Environment names.
- A tag, malformed digest, or missing required file fails before token creation or dispatch.
- The action accepts no app-name, host, arbitrary target repository/ref, or private age-key input.
- No token, bundle, or runtime secret is returned through an action output or logged in a validation error.
- The app-side usage contract pins the action by a full reviewed commit SHA.

## Source reference

REL-05, REL-09, REL-11; SEC-08, SEC-09, SEC-14; v5 §§7.2, 12.2.

## Verify

- Run focused tests for valid inputs, each invalid Environment, tag references, malformed digests, and absent files.
- Inspect action metadata and logs to confirm no identity/host override input or secret-valued output exists.
- Run the repository's workflow/action lint on the new metadata and test workflow.

## Out of scope

Bundle encryption, OIDC token creation, dispatch, polling, app workflow implementation, and live deployment acceptance.
