# Spec 02: Dispatch and OIDC Trust Proof

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 02 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review |
| Depends on | `01_foundation-and-access` (its checklist must be complete before this spec is implemented) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (`DEP`), `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (`SEC`) |
| Design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` §§4.5, 7.2, 8.1–8.2, 16 step 2, 17 item 1; `docs/design/infrastructure-contracts-and-invariants.md` §§1–3, 6; `docs/design/variables-and-secrets.md` §§2, 5.3 |

## What

Before building the privileged deployment pipeline, prove with a disposable app repository that an app workflow can obtain a request-bound GitHub OIDC token, authenticate a cross-repository `workflow_dispatch` using the dispatch-only GitHub App, and trigger a harmless CentralDevOps Staging workflow from a non-main branch. The proof verifies the source repository, workflow, ref, Environment, audience binding, dispatch actor, and matching CentralDevOps Environment. It uses no deployment credential and does not connect to a VPS. This is an acceptance spike, not the production authorizer or deploy workflow.

## Context

- The platform keeps privileged deployment code and server credentials in CentralDevOps. The app's OIDC token identifies and binds the request to its workflow run and payload; the GitHub App installation token independently authorizes the cross-repository dispatch. An app-context reusable workflow does not provide this trust boundary.
- The roadmap requires spec 01 to be fully checked off before implementation. Its protected `main` and `release/*` branches and CentralDevOps `Staging` and `Production` Environments are prerequisites. Spec 02 may be reviewed before then, but no test resources may be created and no proof may be run until the dependency is verified.
- The proof uses one clearly identified throwaway app repository and synthetic values. It must not use application data, app runtime secrets, SSH keys, age private keys, provider passwords, registry credentials, or VPS access.
- The disposable app has `Staging` and `Production` Environments but no secrets. The positive dispatch uses `Staging`; CentralDevOps `Production` is exercised only if its existing approval gate can be honored without creating secrets or changing its protection.
- The proof uses a small inline repository-to-app fixture. It does not create or depend on the production app registry, which belongs to spec 06.

## Requirements

| ID | Statement | Source |
|---|---|---|
| T-01 | A disposable app repository dispatches a harmless CentralDevOps `workflow_dispatch` run from a non-main Staging-allowed branch using an installation token from the dispatch-only GitHub App. | DEP-20, SEC-10, DEP-16 |
| T-02 | The source workflow requests an OIDC token whose audience binds the exact target Environment, `image_ref`, and sealed bundle using the v5 contract: `centraldevops-deploy:` plus the lowercase hexadecimal SHA-256 digest of `UTF-8(environment) \| UTF-8(image_ref) \| bundle_bytes`. The literal separators are `|` bytes, the bundle is the exact byte sequence before base64 transport encoding, and no newline or normalization is added. | DEP-20; v5 §§7.2, 8.1 |
| T-03 | Before Environment selection, CentralDevOps verifies the token signature against GitHub's published JWKS and validates issuer, expiry, audience, required claims, and the exact expected repository, `.github/workflows/deploy.yml`, allowed ref, source Environment, and dispatch payload. It records the verified `repository`, `job_workflow_ref`, `ref`, `environment`, `run_id`, and `run_attempt`, but never records the token. | DEP-20, DEP-02 |
| T-04 | CentralDevOps independently checks the dispatch actor from trusted event context against the expected GitHub App identity. It derives the source app only from the verified OIDC `repository` claim; neither the app name nor repository is accepted as a caller-supplied identity input. | SEC-10; v5 §§8.1–8.2 |
| T-05 | Only after authorization succeeds may a harmless dependent job select the matching CentralDevOps `Staging` or `Production` Environment. The job proves the Environment association and reads or creates no Environment secret. | DEP-20, DEP-06, DEP-08 |
| T-06 | Invalid signature, issuer or expiry; audience mismatch; altered payload; wrong repository, workflow, ref or Environment; an unexpected dispatch actor; and a CentralDevOps ref not permitted by the requested Environment are rejected before the Environment-bound job starts. Rejection output names the failed check without printing the JWT or bundle. | DEP-02, DEP-16; v5 §8.1 |
| T-07 | The proof produces reproducible, sanitized evidence (run URLs, expected and observed non-secret claims, check results, and date), then removes or revokes all test-only resources and credential access. No JWT, installation token, private key, or bundle contents are committed, logged, or uploaded. | DEP-20, SEC-12 |
| T-08 | The disposable app's `Production` Environment has no required reviewers and accepts only `main` and any explicitly approved release refs. It has no secrets; the single deployment approval remains in CentralDevOps. | SEC-15; `docs/design/variables-and-secrets.md` §2 |

## Design

### Test topology

```text
Disposable app repository
  Staging and Production Environments (no secrets)
  minimal .github/workflows/deploy.yml
    creates synthetic sealed-bundle bytes
    requests request-bound OIDC token
    dispatches CentralDevOps using GitHub App installation token
                  |
                  v
CentralDevOps (Staging: any branch; Production: release/*)
  proof workflow: authorize (no Environment or secrets)
                  -> environment-check (matching Environment, no secret reads)
```

Create one dedicated, clearly named throwaway repository under the organization. It contains no production application source or credentials. The app-side workflow has only `contents: read` and `id-token: write` permissions. Grant access to any temporary GitHub App credentials only to this repository through selected-repository org secrets, or use a short-lived equivalent approved for the test. The GitHub App is installed only on CentralDevOps and has only `Actions: read and write` plus GitHub's automatically required metadata access.

Configure the disposable app's `Staging` and `Production` Environments without secrets. Its `Production` Environment has no required reviewers and is restricted to `main` and any explicitly approved release refs; the proof does not add an app-side approval gate. Use a reviewed `main` ref for the positive workflow run.

Use a fixed synthetic image digest and synthetic sealed-bundle bytes. For the audience, compute SHA-256 over the following exact byte sequence:

```text
UTF-8(target_environment) || 0x7c || UTF-8(image_ref) || 0x7c || sealed_bundle_bytes
```

The audience is `centraldevops-deploy:` followed by the lowercase hexadecimal digest. Transport the bundle as base64 in the dispatch input; the central verifier decodes it exactly once before recomputing the audience. Reject malformed bundle encoding. The dispatch contains only `target_environment`, `image_ref`, the OIDC token, and the synthetic bundle. Do not log the token or bundle.

The CentralDevOps proof workflow is separate from all infrastructure and deployment workflows and follows the selected Environment's branch policy: any branch for `Staging`, and `release/*` only for `Production`. It has minimal explicit permissions. Its `authorize` job has no Environment and no secret access. It verifies the OIDC token and request binding, derives the app from the verified `repository` claim using the inline fixture, and independently checks the dispatch actor. Only after every check passes may a second harmless job select the validated matching CentralDevOps Environment. That job reads no secrets and performs no deployment action.

Mask tokens before use and do not dump `github.event`, request payloads, or verifier inputs. Do not place a JWT, installation token, or bundle in a step output, job output, artifact, run summary, or committed fixture. Keep proof-only code separate from production deployment code and remove it after evidence is captured.

### Negative cases

The verifier tests or controlled dispatches must show rejection of:

- Invalid signature, issuer, expiry, missing required claims, or malformed audience.
- An audience that does not match the recomputed Environment, image reference, and bundle bytes.
- An image reference or bundle changed after token issuance.
- An unregistered repository or a workflow other than that repository's `.github/workflows/deploy.yml`.
- A ref outside the app's allowed-ref fixture, a CentralDevOps ref not permitted by the requested Environment (for example, `main` with `Production`), or a source OIDC `environment` claim that differs from `target_environment`.
- A dispatch actor other than the installed dispatch App.

Use generated keys and synthetic claims for deterministic verifier tests; never put live JWTs in fixtures. Exercise live negative dispatches only where they are safe and meaningful. For claims that cannot be forged in a GitHub-issued token, document the deterministic test and why a live dispatch is not applicable. For every live rejection, verify the Environment-bound job did not start.

### Evidence

Store a concise proof report in `summaries/task-5-summary.md` after the test and cleanup. Include:

- Date, repository names, tested Environment, workflow run URLs, and the CentralDevOps commit tested.
- Expected and observed non-secret claims, audience comparison result, and the check that rejected each negative case.
- Positive and negative outcomes, including confirmation that rejected live requests never entered the Environment-bound job.
- Confirmation that no deployment credential, VPS access, or Environment secret was used.
- Cleanup confirmation for the disposable repository, proof-only code, and test-only credential access.

Do not treat a successful `workflow_dispatch` alone as proof. The report must show both independent authentication checks, request binding, and matching Environment selection. Write each task's `summaries/task-<n>-summary.md` only when that task closes; keep summaries sanitized.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Use a disposable organization repository and synthetic app workflow. | Test from an existing production app; mock all GitHub claims locally | A real dispatch is needed to validate GitHub's claims and Environment behavior; synthetic content avoids exposing application or runtime data. | Yes |
| D2 | Keep authorization and Environment association in separate jobs. | Put OIDC verification in an Environment-bound job | Authorization must not gain Environment secrets or wait for approval before validating the short-lived token. | Yes |
| D3 | Install the dispatch GitHub App only on CentralDevOps and expose temporary credentials only to the disposable app repository. | Install the App on every app repo; use a PAT | CentralDevOps is the dispatch target, selected-repository access limits exposure, and SEC-10 prohibits a PAT. | Yes |
| D4 | Use a no-secret `Staging` Environment for the positive proof; exercise `Production` selection only if the existing approval gate can be honored without creating credentials or weakening its rule. | Create production credentials or remove the approval rule to simplify testing | The test needs no production secrets, and spec 01's gate must remain intact. | Yes |
| D5 | Treat cleanup as part of acceptance and preserve only sanitized evidence. | Keep the disposable repository indefinitely | Temporary access and test artifacts must not become an undocumented permanent trust path. | Yes |
| D6 | Hash the exact sealed-bundle bytes before base64 transport, with UTF-8 Environment and image-reference values and literal `|` separators. | Hash a normalized or re-encoded payload | Both sides must bind the same immutable request bytes without newline or serialization ambiguity. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| The app workflow never receives a server credential and never connects to a VPS. | Review its permissions, secret references, steps, and run evidence; confirm no VPS or deployment secrets were created. |
| Central authorization runs before any Environment is selected. | Workflow graph shows `authorize` has no `environment`; the Environment-bound job depends on successful authorization. |
| A valid OIDC proof and dispatch App identity are both required. | Positive test records each independently; negative cases fail when either proof is absent or wrong. |
| The token binds to the exact Environment, digest, and sealed-bundle bytes. | Recompute the audience from the canonical byte sequence; changed payload cases fail before Environment selection. |
| CentralDevOps runs comply with the selected Environment's branch policy. | A non-main Staging dispatch can reach the harmless Environment-bound job; a Production dispatch from outside `release/*` cannot. |
| The app's `Production` Environment adds no second approval gate and allows only approved refs. | Audit shows no required reviewers and only `main` plus any explicitly approved release refs; no secrets are present. |
| No token or bundle contents leak to logs or artifacts. | Review run logs, uploaded artifacts, summaries, and committed files. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Spec 01 checklist is incomplete or its required protections and Environments cannot be verified. | Do not implement or run this proof. Record the dependency as blocked; do not substitute a weaker Environment or branch gate. |
| GitHub App credentials or installation permissions are unavailable. | Stop the proof and report the exact missing permission or scope; do not use a PAT or broader credential. |
| OIDC verification fails or a claim does not match. | Fail authorization with a non-sensitive check identifier; do not start the Environment-bound job and do not print the token. |
| The CentralDevOps ref is not permitted by the requested Environment, or the actor is unexpected. | Reject before Environment selection. |
| A test accidentally creates or exposes a deployment credential or secret. | Stop, revoke or remove the exposed test value, preserve only sanitized diagnostic evidence, and report the incident; do not continue the proof. |
| Temporary GitHub resources cannot be removed. | Record the exact remaining resource and access, revoke its credentials immediately, and leave the proof incomplete until cleanup is verified. |

## Testing Strategy

- **Positive dispatch:** A throwaway app `deploy.yml` on `main` targets `Staging` with synthetic inputs, and dispatches the CentralDevOps proof workflow from a non-main test branch. Confirm the GitHub App dispatch succeeds, OIDC claims and audience verify, and the CentralDevOps `Staging` Environment-bound job is selected.
- **Independent proof checks:** Exercise a wrong dispatch actor and an invalid OIDC proof; each must fail before Environment selection.
- **Binding and claim negatives:** Exercise audience, digest, bundle, repository, workflow, ref, and Environment mismatch cases. Confirm none starts the Environment-bound job; use deterministic verifier tests where GitHub-issued claims cannot safely be forged.
- **No-secret audit:** Inspect workflow permissions, secret references, run logs, artifacts, and temporary GitHub resources. Confirm no deploy/server credentials were created or used and no token or bundle was printed or uploaded.
- **Evidence and cleanup:** Review the sanitized proof report and verify all test-only resources and credentials were removed or revoked.

## Out of Scope

- Production `deploy-app.yml`, the production OIDC verifier, replay store, registry lookup, digest policy, attestation verification, or deployment authorization implementation (spec 10).
- App-side shared `request-deploy` action, sealing implementation, and production `deploy.yml` (spec 12).
- Any SSH key, age private key, runtime secret, deploy credential, registry token, host, VPS, or application deployment.
- Creating production GitHub App credentials or org-level secrets for real app repositories.
- Implementing the full negative authorization suite for the production deployment pipeline; this proof establishes the trust contract and its core rejection boundaries only.
