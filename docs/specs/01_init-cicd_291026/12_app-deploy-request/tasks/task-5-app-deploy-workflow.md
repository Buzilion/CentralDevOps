# Task 5: App deploy workflow

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` |
| Depends on | Tasks 1 to 4 |
| Needs | Spec 09 build workflow pattern; app `Staging` and `Production` Environments and their app-owned runtime values |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Add the app-owned manual deploy workflow that renders the selected Environment's runtime values and calls the reviewed shared action without copying privileged logic.

## Relevant files or references

- Create `<app-repository>/.github/workflows/deploy.yml`
- Use the app-owned `compose.yml` and `deploy/staging.yml`, `deploy/production.yml`
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-01, REL-05 to REL-11)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-08, SEC-09, SEC-14, SEC-15)
- `docs/design/infrastructure-contracts-and-invariants.md` §§2–4
- v5 design §§7.2, 12.2

## Proposed approach

1. Add a `workflow_dispatch`-only `deploy.yml` with exactly two operator inputs: the `Staging`/`Production` choice and the full digest string. Do not add a build trigger, tag input, app name, host, or rollback mode.
2. Set the app job's GitHub Environment to the selected target so only that Environment's app values are available. Configure the app Production Environment for allowed refs without adding a second reviewer gate by default.
3. Grant only `contents: read` and `id-token: write`. Pin the CentralDevOps request action and any third-party actions to reviewed full commit SHAs.
4. Map `Staging` to `deploy/staging.yml` and `Production` to `deploy/production.yml` without accepting an arbitrary path. Expose app-owned `APP_*` variables/secrets only to the rendering step, mask values before use, and render only the manifest's declared runtime keys with the central-compatible dotenv serializer. Do not evaluate the file or print any value.
5. Write the runtime file under the runner temporary directory with restrictive permissions, pass only its path plus the Compose and manifest paths to the shared action, and remove temporary plaintext after the action completes.
6. Confirm the app's separate `build.yml` remains manual and is not called by `deploy.yml`. After spec 09, the app must have exactly the two workflows required by REL-01.
7. Implement in the designated app repository. If acceptance uses a disposable app, keep it isolated and do not turn it into the deferred REL-16 starter-template product.

## Acceptance criteria

- `deploy.yml` is manual-only and has exactly the two specified inputs and no auto-build/deploy chaining.
- The app deploy job uses the matching GitHub Environment and minimum permissions.
- Runtime file keys exactly match the selected manifest; app secrets are step-scoped and are not printed, uploaded, committed, or passed as workflow-dispatch inputs.
- The action is referenced by full reviewed commit SHA; no sealing, OIDC, dispatch, or polling logic is copied into the app workflow.
- The app Production Environment does not add a second approval by default; central Production approval remains authoritative.
- After spec 09 is applied, the app has exactly one manual `build.yml` and one manual `deploy.yml`.

## Source reference

REL-01, REL-05 to REL-11; SEC-08, SEC-09, SEC-14, SEC-15; v5 §§7.2, 12.2.

## Verify

- Run workflow lint and static inspection of triggers, inputs, permissions, action references, and Environment mapping.
- Exercise the dotenv serializer with synthetic values containing quotes, equals signs, backslashes, and supported multiline content; confirm round-trip equality without logging values.
- Inspect the temporary file lifecycle and run logs using synthetic canary secrets.
- Confirm invalid tags fail before dispatch and the build workflow remains a separate manual operation.

## Out of scope

Build workflow implementation, app-source changes, central authorization or deployment code, and starter-template delivery.
