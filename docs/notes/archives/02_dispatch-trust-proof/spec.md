# Spec 02: Dispatch and OIDC Trust Proof

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 02 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review |
| Depends on | `01_foundation-and-access` (its checklist must be complete before this spec is implemented) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (`DEP`), `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (`SEC`) |
| Design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` §§4.5, 7.2, 8.1–8.2, 16 step 2, 17 item 1; `docs/design/infrastructure-contracts-and-invariants.md` §§1–3, 6 |

## What

Before building the privileged deployment pipeline, prove with a disposable app repository that an app workflow can obtain a request-bound GitHub OIDC token, authenticate a cross-repository `workflow_dispatch` using the dispatch-only GitHub App, and trigger a harmless workflow in CentralDevOps on `main`. The test must verify the source repository, workflow, ref, Environment, audience binding, dispatch actor, and matching CentralDevOps Environment without accessing a VPS or any deployment credential. This is an acceptance spike, not the production authorizer or deploy workflow.

## Context

The platform's trust boundary requires app repositories to request deployments while all privileged deployment code and server credentials remain in CentralDevOps. The app and central dispatch provide two independent proofs: the OIDC token identifies and binds the request to the app run and payload; the GitHub App installation token permits the cross-repository dispatch. An app-context reusable workflow would not provide this boundary.

The roadmap places this proof before host bootstrap and before the full deployment pipeline. Spec 01 establishes the repository protections and `Staging`/`Production` Environments this spike relies on. Its checklist is currently unchecked; this spec may be reviewed now, but implementation remains blocked until spec 01 is complete.

The proof uses only a throwaway repository and synthetic payloads. It must not create or use SSH keys, age private keys, provider passwords, runtime secrets, registry credentials, or VPS access. Any GitHub App credentials used by the app test are limited to dispatch and exposed only to the disposable test repository through selected-repository secret access.

## Requirements

| ID | Statement | Source |
|---|---|---|
| T-01 | A disposable app repository can dispatch a harmless CentralDevOps `workflow_dispatch` run on the protected `main` branch using an installation token from the dispatch-only GitHub App. | DEP-20, SEC-10, DEP-16 |
| T-02 | The source workflow requests an OIDC token with an audience derived from `target_environment`, the exact `image_ref`, and the exact sealed-bundle bytes using the v5 contract: `centraldevops-deploy:` plus the SHA-256 of `environment \| image_ref \| bundle`. | DEP-20; v5 §§7.2, 8.1 |
| T-03 | The central-side proof records, without recording the token, the verified `repository`, `job_workflow_ref`, `ref`, `environment`, `run_id`, and `run_attempt` claims, and confirms they match the disposable app's expected repository, `.github/workflows/deploy.yml`, allowed ref, selected Environment, and dispatch payload. | DEP-20, DEP-02 |
| T-04 | The central workflow confirms the dispatch actor is the expected GitHub App identity, independently of the OIDC proof. The app repository and app name are not accepted as caller-supplied identity claims; the repository is derived from the verified token. | SEC-10; v5 §§8.1–8.2 |
| T-05 | The central workflow selects only the matching CentralDevOps `Staging` or `Production` Environment after the no-secret authorization job succeeds. The test proves the Environment association; it does not read or create Environment secrets. | DEP-20, DEP-06, DEP-08 |
| T-06 | Invalid signature/issuer/expiry, audience mismatch, altered payload, wrong repository, workflow, ref or Environment, and an unexpected dispatch actor are rejected before the Environment-bound job starts. Rejection output identifies the failed check without printing the JWT or bundle. | DEP-02, DEP-16; v5 §8.1 |
| T-07 | The test records reproducible, sanitized evidence (run URLs, expected and observed non-secret claims, check results, and date) sufficient to show the dispatch and matching Environment selection worked. No JWT, installation token, private key, or bundle contents are committed, logged, or uploaded. | DEP-20, SEC-12 |

## Design

### Test topology

```text
Disposable app repository
  Staging environment
  minimal .github/workflows/deploy.yml
    creates synthetic sealed-bundle bytes
    requests request-bound OIDC token
    dispatches CentralDevOps using GitHub App installation token
                  |
                  v
CentralDevOps (main)
  proof workflow: authorize (no Environment or secrets)
                  -> environment-check (matching Environment, no secrets)
```

Create a dedicated, clearly named throwaway repository under the organization. It contains no production application source or credentials. Its workflow has only `contents: read` and `id-token: write` permissions. Grant access to the dispatch App credentials only to this repository using selected-repository org secrets, or use a short-lived equivalent approved for the test. The GitHub App installation itself is limited to CentralDevOps and has only `Actions: read and write` plus GitHub's automatically required metadata access.

The disposable workflow runs from a reviewed `main` ref and declares the app-side `Staging` Environment. Use a fixed synthetic image digest and non-secret synthetic bundle bytes. Compute the audience from the exact bytes sent in the dispatch payload; do not log the token or bundle. The dispatch contains only `target_environment`, `image_ref`, the OIDC token, and the synthetic bundle, matching the future request shape.

The CentralDevOps proof workflow runs from `main`, is separate from all infrastructure and deployment workflows, and has no access to an Environment or secrets in its authorization job. It verifies the OIDC signature against GitHub's published JWKS and validates issuer, expiry, audience, required claims, and the exact expected workflow/ref/Environment. It derives the app identity from the verified `repository` claim. Independently, it checks that the dispatch actor is the installed GitHub App. Only after every check passes may a second, harmless job associate itself with the verified matching CentralDevOps Environment. That job reads no secrets and performs no deployment action.

Keep the proof implementation disposable: use a dedicated proof workflow and test code rather than adding production deployment behavior or weakening the eventual production authorizer contract. Remove the throwaway repository and test-only credentials after collecting evidence, using a documented cleanup procedure that names only the exact disposable resources.

### Negative cases

The test suite or controlled dispatches must show the authorization job rejects:

- Invalid signature, issuer, or expired token.
- An audience that does not match the recomputed environment, image reference, and bundle.
- A changed image reference or bundle after token issuance.
- An unregistered repository or a workflow other than that repository's `.github/workflows/deploy.yml`.
- A ref outside the app's allowed-ref fixture.
- A source OIDC `environment` claim that differs from `target_environment`.
- A dispatch actor other than the installed dispatch App.

For each rejection, verify the Environment-bound job did not start. Do not copy test JWTs into fixtures; generate short-lived tokens during the controlled run, and use safe synthetic values for any mutation tests.

### Evidence

Store a concise proof report under this spec's `summaries/` directory, with no credentials or token material. Include:

- Date, repository names, tested Environment, workflow run URLs, and the CentralDevOps commit tested.
- Expected and observed non-secret claims and audience comparison result.
- Positive and negative case outcomes, including confirmation that rejected requests never entered the Environment-bound job.
- Confirmation that no deployment credential, VPS access, or secret value was used.
- Cleanup confirmation for the disposable repository and test-only credentials.

Do not treat a successful `workflow_dispatch` alone as proof: the report must show both independent authentication checks, the OIDC request binding, and the Environment selection.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Use a disposable organization repository and synthetic app workflow. | Test from an existing production app; mock the GitHub claims locally | A real dispatch is needed to validate GitHub's claims and Environment behavior; synthetic content avoids exposing application or runtime data. | Yes |
| D2 | Keep authorization and Environment association in separate jobs. | Put OIDC verification in an Environment-bound job | The authorization job must not gain Environment secrets or wait for approval before validating the short-lived token. | Yes |
| D3 | Install the dispatch GitHub App only on CentralDevOps; expose its credentials to the disposable app repository only for the test. | Install the App on every app repo; use a PAT | CentralDevOps is the dispatch target, selected-repository credentials limit exposure, and SEC-10 prohibits a PAT. | Yes |
| D4 | Use only a no-secret `Staging` Environment for the positive selection proof; exercise `Production` selection only if the required approval gate can be tested without creating credentials or weakening its rule. | Create production credentials or remove the approval rule to simplify testing | The test does not need production secrets, and must not weaken spec 01's gate. | Yes |
| D5 | Treat cleanup as part of acceptance; preserve only sanitized evidence. | Keep the disposable repository indefinitely | Temporary access and test artifacts should not become an undocumented permanent trust path. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| The app workflow never receives a server credential and never connects to a VPS. | Review its permissions, secret references, steps, and run evidence; confirm no VPS or deployment secrets were created. |
| Central authorization runs before any Environment is selected. | Workflow graph shows authorization has no `environment`; the Environment-bound job depends on successful authorization. |
| A valid OIDC proof and dispatch App identity are both required. | Positive test records each independently; negative cases fail when either proof is absent or wrong. |
| The token binds to the exact Environment, digest, and bundle. | Recompute and compare the audience; modified payload cases fail before Environment selection. |
| CentralDevOps uses only the reviewed `main` workflow. | Dispatch run records its ref as `refs/heads/main`; a non-main dispatch cannot reach the Environment-bound job. |
| No token or bundle contents leak to logs or artifacts. | Review run logs, uploaded artifacts, and the sanitized evidence report. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Spec 01 checklist is incomplete or its required protections/Environments cannot be verified. | Do not implement or run this proof. Record the dependency as blocked; do not substitute a weaker Environment or branch gate. |
| GitHub App credentials or installation permissions are unavailable. | Stop the proof and report the exact missing permission or scope; do not use a PAT or broader credential. |
| OIDC verification fails or a claim does not match. | Fail authorization with a non-sensitive check identifier; do not start the Environment-bound job and do not print the token. |
| CentralDevOps dispatch is not from `main` or actor is unexpected. | Reject before Environment selection. |
| Any test accidentally creates or exposes a deployment credential or secret. | Stop, revoke/remove the exposed test value, preserve only sanitized diagnostic evidence, and report the incident; do not continue the proof. |
| Temporary GitHub resources cannot be removed. | Record the exact remaining resource and access, revoke its credentials immediately, and leave the proof incomplete until cleanup is verified. |

## Testing Strategy

- **Positive dispatch:** A throwaway app `deploy.yml` on `main` targets `Staging` using synthetic inputs. Confirm the GitHub App dispatch succeeds, OIDC claims and audience verify, and the CentralDevOps `Staging` Environment-bound job is selected.
- **Independent proof checks:** Repeat with a wrong dispatch actor and with an invalid OIDC proof; each must fail before Environment selection.
- **Binding and claim negatives:** Exercise audience, digest, bundle, repository, workflow, ref, and Environment mismatch cases. Confirm none starts the Environment-bound job.
- **No-secret audit:** Inspect workflow permissions, secret references, run logs, artifacts, and temporary GitHub resources. Confirm no deploy/server credentials were created or used and no token or bundle was printed or uploaded.
- **Evidence and cleanup:** Review the sanitized proof report and verify all test-only resources and credentials were removed or revoked.

## Out of Scope

- Production `deploy-app.yml`, the production OIDC verifier, replay store, registry lookup, digest policy, attestation verification, or deployment authorization implementation (spec 10).
- App-side shared `request-deploy` action, sealing implementation, and production `deploy.yml` (spec 12).
- Any SSH key, age private key, runtime secret, deploy credential, registry token, host, VPS, or application deployment.
- Creating production GitHub App credentials or org-level secrets for real app repositories.
- Implementing the full negative authorization suite for the production deployment pipeline; this proof establishes the trust contract and its core rejection boundaries only.
