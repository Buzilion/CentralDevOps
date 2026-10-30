# Task 3: OIDC-bound dispatch

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` |
| Depends on | Tasks 1 and 2 |
| Needs | Spec 02 proof contract; dispatch GitHub App installed only on CentralDevOps with `actions: write` |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Bind the exact sealed request to the app workflow run and dispatch the CentralDevOps deployment workflow using only the dispatch App.

## Relevant files or references

- `.github/actions/request-deploy/action.yml` and its helper code
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` (T-02 to T-06)
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-08, REL-09, REL-12)
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (DEP-02, DEP-03, DEP-16)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-10, SEC-14)
- v5 design §§4.5, 7.2, 8.1

## Proposed approach

1. Hash the exact bytes `UTF-8(target_environment) || 0x7c || UTF-8(image_ref) || 0x7c || sealed_bundle_bytes`, with no newline or normalization. Request the GitHub OIDC token using audience `centraldevops-deploy:` plus the lowercase hexadecimal SHA-256 digest.
2. Create a short-lived installation token from `DEPLOY_DISPATCH_APP_ID` and `DEPLOY_DISPATCH_APP_PRIVATE_KEY`. Scope it to the CentralDevOps installation. Do not use a PAT or print either credential or the resulting token.
3. Dispatch only CentralDevOps `deploy-app.yml` on a ref permitted by the requested Environment (`Staging`: any branch; `Production`: `release/*` only) with the Environment, digest, OIDC token, and base64 bundle. Include the source `run_id` and `run_attempt` from the GitHub run context as correlation metadata; spec 10 must require exact equality with the verified OIDC claims.
4. Before the API call, serialize the complete UTF-8 dispatch request body, including `ref`, all inputs, the OIDC token, and base64 bundle. Reject requests larger than 64,000 bytes (or a lower verified GitHub limit) before sending them. Report size and cap only; do not dump the serialized payload.
5. Keep the dispatch actor, installation, and workflow/ref checks independent of OIDC identity checks. Do not send an app name or treat correlation metadata as authorization.
6. Use deterministic synthetic tests for audience bytes, base64 round-trip, input tampering, boundary payload sizes, and API-call suppression on oversize or token failure.

## Acceptance criteria

- The requested OIDC audience matches the Spec 02 formula byte-for-byte, including exact Environment and image-reference encoding and pre-base64 bundle bytes.
- Changing the Environment, digest, or any bundle byte changes the audience and causes central authorization to reject a stale proof.
- The dispatch uses a short-lived GitHub App installation token with only the required CentralDevOps Actions access; no PAT path exists.
- The API request explicitly targets `deploy-app.yml` on a ref permitted by the requested Environment and contains no plaintext runtime secret or app-name input.
- Source run ID and attempt are supplied only for correlation and are required to match the verified OIDC claims centrally.
- The full serialized request is rejected before the API call above the cap; the error contains no token or bundle content.

## Source reference

REL-08, REL-09, REL-12; DEP-02, DEP-03, DEP-16; SEC-10, SEC-14; Spec 02 T-02 to T-06.

## Verify

- Recompute the audience independently from synthetic test bytes and compare it with the requested audience.
- Change each bound field and one bundle byte in turn; confirm that the original proof no longer verifies.
- Test request bodies below, at, and above the configured cap; assert the oversized cases make no HTTP dispatch call.
- Inspect logs and artifacts for absence of tokens, serialized payloads, and bundle contents.

## Out of scope

Central authorization implementation, polling, app workflow rendering, and production credential provisioning.
