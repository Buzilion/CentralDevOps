# Spec 12: App Deploy Request

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 12 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation blocked until specs 10 and 11 are complete |
| Depends on | `10_deploy-authorization` and `11_deploy-execution-and-rollback` (each checklist must be complete before this spec is implemented) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL`), `access-and-secrets-v1.md` (`SEC`), `central-deployment-v1.md` (`DEP`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§1–3, 6–7; `docs/design/naming-and-repository-conventions.md` §§4, 6, 8; `docs/design/variables-and-secrets.md` §§4.4, 5.1–5.3; v5 design §§4.5, 5.2, 7.2, 8.1–8.4, 12.2, 15.2–15.6, 16 step 9, 17 item 1 |

## What

Deliver the shared CentralDevOps `request-deploy` action and the app-side manual `deploy.yml` pattern. The action validates the requested digest, seals the app's runtime configuration, binds the exact request to the app run's OIDC identity, dispatches CentralDevOps, and reports the central run's result. An operator rolls back by running the same deploy operation with a previous known-good digest.

The app repository remains unprivileged: it never connects to a VPS and never receives a deploy SSH key, registry pull token, or age private key.

## Context

- The roadmap's numeric order still applies. Drafting this spec does not permit skipping specs 09–11. Implementation is blocked until the checklists for specs 10 and 11 are complete.
- Spec 09 owns the app build and provenance pattern. This spec consumes the full digest copied from that build; it does not build an image, deploy a tag, or automatically start the build workflow.
- Spec 10 owns central request authorization and replay protection. Spec 11 owns the privileged deployment, health-check rollback and deployment record. This spec implements only the app-side request and shared request action; it must use those central contracts rather than duplicate or bypass them.
- Spec 02 proves the dispatch and OIDC trust pattern with synthetic data. Reuse its exact audience-byte contract and do not reuse its proof-only workflow or fixtures as production authorization.
- The app reads runtime values from its matching GitHub Environment. Make secrets available only to the rendering step; after GitHub injects them, they may exist in that runner process and in a restricted temporary file only until sealing. They are never workflow inputs, artifacts, logs, summaries, or committed files.
- The matching age private key and deploy credentials remain in CentralDevOps. The app uses only committed public age recipients and its selected-repository GitHub App credentials.

## Requirements

| ID | Statement | Source |
|---|---|---|
| REL-01 | Each app has exactly two separate manual workflows: `build.yml` from spec 09 and `deploy.yml` from this spec. Neither starts the other automatically. | App Release PRD REL-01; v5 §§7.1–7.2 |
| REL-05 | `deploy.yml` accepts exactly `target_environment` (`Staging` or `Production`) and a full digest `image_ref`. Tags and malformed references fail before dispatch. | App Release PRD REL-05; v5 §7.2 |
| REL-06 | The deploy job has least-privilege permissions and reads runtime variables and secrets only from the matching app Environment to create the runtime environment file. | App Release PRD REL-06; SEC-08 |
| REL-07 | The request seals `runtime.env`, `compose.yml`, and the selected Environment's route manifest to that Environment's age recipient. The dispatch contains no plaintext runtime secret. | App Release PRD REL-07; SEC-08; v5 §7.2 |
| REL-08 | The request's OIDC audience binds the exact target Environment, `image_ref`, and sealed-bundle bytes. A changed value or bundle cannot retain a valid request binding. | App Release PRD REL-08; DEP-02; Spec 02 T-02 |
| REL-09 | A dispatch-only GitHub App token dispatches CentralDevOps `deploy-app.yml`. The app identity is derived centrally and is not a request input. | App Release PRD REL-09; SEC-10 |
| REL-10 | The app run waits for its corresponding central run, fails when that run fails, and reports the central run URL without runtime values. | App Release PRD REL-10; v5 §§7.2, 15.3 |
| REL-11 | Apps call the shared CentralDevOps `request-deploy` action by a reviewed full commit SHA rather than copying its sealing, identity, dispatch, or polling logic. | App Release PRD REL-11; SEC-14 |
| REL-12 | The action detects an oversized serialized dispatch request before sending it and explains the limit without exposing the bundle. This spec resolves Q11: there is no alternate transport in v1; the request fails closed. | App Release PRD REL-12; parent PRD Q11; v5 §7.2 |
| REL-13 | Manual rollback reruns `deploy.yml` with the previous known-good digest; it does not introduce a tag-based or separate rollback path. | App Release PRD REL-13; v5 §§8.4, 15.6 |
| REL-14 | The operator flow documents build, Staging verification, Production deployment, and digest-based rollback. | App Release PRD REL-14; v5 §§15.2–15.3, 15.6 |
| SEC-08 | App runtime secrets stay in the app's matching Environment and are encrypted in transit; they are not exposed through inputs, artifacts, logs, or summaries. | Access and Secrets PRD SEC-08 |
| SEC-09 | No app repository or app Environment contains the registry pull token or deploy SSH key. | Access and Secrets PRD SEC-09 |

REL-02 to REL-04 and REL-15 remain owned by spec 09. Authorization and central-side validation remain owned by spec 10; deployment execution and automatic rollback remain owned by spec 11.

## Design

### App workflow and runtime environment

- An onboarded app has one manual `build.yml` and one manual `deploy.yml`. `deploy.yml` has only a `workflow_dispatch` trigger with exactly two operator inputs:

  | Input | Type and allowed value |
  |---|---|
  | `target_environment` | Choice: `Staging` or `Production` |
  | `image_ref` | String: full `ghcr.io/<OWNER>/<IMAGE>@sha256:<64-hex-digest>` |

- The operator copies `image_ref` from the build run summary. `deploy.yml` does not invoke `build.yml`; rollback uses the same workflow and an earlier digest.
- The request job selects the app's GitHub Environment matching `target_environment`. App Production Environment branch restrictions follow SEC-15 and add no second reviewer gate by default; the CentralDevOps Production Environment remains the approval gate.
- The job grants only `contents: read` and `id-token: write`. Validate the digest before sealing or dispatch. CentralDevOps still performs the authoritative registry, repository, ref, and digest checks.
- Render only the runtime keys declared by the selected manifest, using that Environment's app-owned `APP_*` variables and secrets exposed to that step only. Mask values before use. Reject missing, extra, reserved, or duplicate keys. Serialize values with the same dotenv contract consumed centrally; do not evaluate or shell-source the generated file. Write it under the runner temporary directory with restrictive permissions and never print it.
- The app workflow calls `.github/actions/request-deploy/action.yml` in CentralDevOps by full reviewed commit SHA. It contains no copy of action logic and no server connection, host selection, or credential.

### Shared action and sealed request

The action's stable interface takes the Environment, digest, paths to the rendered runtime file, Compose file and selected manifest, and the dispatch App ID/private key. It returns only sanitized `central_run_url` and `central_run_result` outputs; the result is one of `success`, `failure`, `cancelled`, `timed_out`, or `unknown`, never a remote log message. Only a central `success` conclusion may produce `success`. The central repository/workflow/ref and age recipient selection are controlled by reviewed action code, not caller inputs. There is no `app_name`, host, arbitrary recipient, private age-key, or rollback input.

The action packages only `runtime.env`, `compose.yml`, and the selected `deploy/staging.yml` or `deploy/production.yml` manifest, then encrypts the bundle for the selected Environment's committed public recipient(s). `Staging` maps to `deploy/staging.yml`; `Production` maps to `deploy/production.yml`. It supports the planned two-recipient overlap during age-key rotation, and spec 11's central decryptor must accept both matching private identities during that overlap. The matching age private key is never present in the app repository. Temporary plaintext and token files use restrictive permissions, are masked as appropriate, and are removed on success and failure; none are uploaded as artifacts.

The OIDC audience is exactly `centraldevops-deploy:` followed by the lowercase hexadecimal SHA-256 digest of:

```text
UTF-8(target_environment) || 0x7c || UTF-8(image_ref) || 0x7c || sealed_bundle_bytes
```

Hash the exact sealed bytes before base64 transport. Do not normalize, re-encode, or append a newline. The central verifier recomputes this same value. The dispatch-only GitHub App installation token independently authorizes a `workflow_dispatch` of CentralDevOps `deploy-app.yml` on `main`; the app name is not sent.

For unambiguous polling, dispatch metadata includes the source `run_id` and `run_attempt` from the GitHub run context. These values are correlation metadata only: spec 10 must compare them with the OIDC claims before authorization, and the OIDC token remains the identity proof. The central run must expose a sanitized correlation value that the action can match through the Actions API; the action must not guess by time, app, Environment, or digest alone.

### Q11 decision: oversized bundle

- Keep the sealed bundle at or below 40 KiB as the operational target. Before dispatch, serialize and measure the complete UTF-8 workflow-dispatch request body, including base64 bundle, OIDC token, inputs, and ref.
- Enforce a conservative 64,000-byte request-body cap, or a lower cap if verification of the current GitHub limit requires it. Reject locally before the dispatch API call when the request exceeds the cap. The message reports the measured size and cap, but no payload or secret.
- There is no v1 fallback to Actions artifacts, object storage, pre-signed URLs, request splitting, or another credential-bearing service. Operators must remove unnecessary material from the runtime bundle. If a valid app needs a larger payload, stop and approve a separately designed transport rather than bypassing the cap.

### Result and rollback

- The action waits for the central run identified by the source run ID and attempt. It refreshes the short-lived App installation token as needed while polling, without redispatching the request. It exits nonzero for a failed, cancelled, or otherwise unsuccessful central conclusion; it never reports success for an unknown or timed-out result. The app run summary includes the central run URL, selected Environment, digest, and sanitized result only.
- Automatic health-check rollback is performed centrally by spec 11. For a manual rollback after a successful deployment, the operator reruns the same app `deploy.yml` with the previous known-good digest. No tag, separate workflow, or app-side SSH operation is allowed.
- The operator guide records the build → Staging → verification → Production flow and the digest-based rollback procedure. Database migrations must remain backward-compatible as specified by the central deployment and database contracts.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Keep the operator interface to exactly two manual inputs: Environment and immutable image digest. | Add app name, host, tag, or build trigger inputs | CentralDevOps derives identity and placement; separate manual operations preserve the reviewed release flow. | Yes |
| D2 | Bind OIDC to the exact Environment, digest, and sealed bytes; hash before base64 transport. | Bind only to a run ID or hash normalized payload data | This prevents changing any deployment input or encrypted bundle after token issuance. | Yes |
| D3 | Reject an oversized request before dispatch; do not add an external fallback transport in v1. | Upload the bundle to an artifact or object store and dispatch a reference | The existing contract is intentionally self-contained; external storage would add credentials, retention, access control, and another trust boundary. | Yes |
| D4 | Use the shared CentralDevOps action pinned by full commit SHA. | Copy action logic into every app workflow or call it by a mutable branch/tag | One reviewed implementation avoids drift and prevents an app from silently changing privileged request logic. | Yes |
| D5 | Carry source `run_id` and `run_attempt` only as correlation metadata and require spec 10 to compare them with the verified OIDC claims. | Poll for a run by approximate creation time, Environment, or digest | A stable exact correlation avoids attaching the app result to another concurrent deployment; metadata alone never authorizes a request. | Yes |
| D6 | Perform manual rollback by rerunning `deploy.yml` with the previous digest. | A separate rollback workflow or mutable rollback tag | It preserves the same authorization, policy, approval, and audit path as a forward deployment. | Yes |
| D7 | During age-key rotation, seal for both the old and new Environment recipient until the transition closes. | Replace the recipient immediately | Both sides of an in-flight transition must remain able to decrypt without exposing a private key to apps. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| Each app has exactly the separate manual build and deploy workflows; neither starts the other. | Inspect workflow triggers and run both manually. |
| Only a full digest reference is accepted. | Submit a tag and malformed digest; each fails before any dispatch. |
| App-side runtime values match the selected manifest and never enter an artifact, log, workflow input, or summary in plaintext. | Use synthetic canary values and inspect logs, artifacts, summaries, and runner cleanup. |
| Only the target Environment's age private key can open the bundle, with the old/new overlap accepted during rotation. | Decrypt in an isolated test with each Environment key and run the rotation overlap test. |
| The request audience binds the exact Environment, digest, and sealed bytes. | Recompute the Spec 02 byte sequence and verify altered values or bytes are rejected centrally. |
| App identity is derived from verified OIDC claims, never from an app-name input. | Inspect the dispatch schema and spec 10 authorization tests. |
| Oversized requests cause no dispatch and no alternate upload. | Test above the cap and inspect the API call log and artifacts. |
| The app run reports the result of its own central run. | Run concurrent synthetic requests and verify each app run links only to its matching source run ID and attempt. |
| The app has no server credentials or direct VPS path. | Audit app secrets, workflow permissions, action inputs, and workflow steps. |

## Error Behavior

| Situation | Behavior |
|---|---|
| `target_environment` is not exactly `Staging` or `Production`, or `image_ref` is malformed or a tag. | Fail before sealing or dispatch with a sanitized field-level message. |
| A required app runtime key is missing, an undeclared/reserved key is present, or a value cannot be serialized by the agreed dotenv contract. | Fail before dispatch; do not print the value or produce a success-shaped bundle. |
| An Environment recipient is missing or age sealing fails. | Fail closed before dispatch; do not use another Environment's recipient or transmit plaintext. |
| The GitHub App token or OIDC token cannot be created. | Fail without dispatch and without logging credentials or token contents. |
| The sealed bundle or full serialized request exceeds the cap. | Reject before the dispatch API call with the measured size and limit; do not upload, split, or retry through another transport. |
| Dispatch response is ambiguous or no unique matching central run is found. | Do not report success or blindly create a duplicate deployment; fail with a sanitized correlation detail and link if known. |
| The central run fails, is cancelled, or does not reach a successful terminal result within the app job's permitted runtime. | Fail the app run and report the central run URL/status if known. Never print the runtime file, bundle, or token. |
| The previous digest is invalid or no longer permitted by central policy. | Let central authorization reject the request; do not bypass the normal deployment path. |

## Testing Strategy

- **Action input tests:** exact Environment choices, full digest-only validation, required file/credential presence, rejection before network access, and no caller-supplied app identity or recipient.
- **Bundle tests:** exact three-file membership, restrictive temporary files, no plaintext artifacts/logs, wrong-Environment decryption failure, successful old/new recipient overlap, and cleanup after both success and failure.
- **Request-binding tests:** recompute the audience from exact bytes; change each bound value independently and confirm central rejection. Use synthetic data for deterministic negative tests; live proof follows the safe pattern from spec 02.
- **Payload tests:** measure the fully serialized request, confirm a valid request under the cap can dispatch, and confirm an oversized request fails before the API call without an artifact or storage fallback.
- **Workflow tests:** exactly two manual workflows, exactly two deploy inputs, least-privilege permissions, matching Environment selection, pinned action SHA, and no automatic build/deploy chaining.
- **Staging acceptance:** deploy by digest, receive the matching central result URL, verify no canary secret in logs/artifacts, then rerun the deploy workflow with the previous known-good digest. Confirm the normal central path and rollback behavior from spec 11.
- **Production gate:** do not weaken either repository's Environment rules to test. Exercise Production only when its required CentralDevOps approval and credentials are available; the app Production Environment must not add a second reviewer gate by default.
- Record sanitized commands, run URLs, outcomes, and date in each task summary. Never record secrets, OIDC tokens, App private keys, sealed bundle contents, or plaintext runtime values.

## Deliverables

```text
.github/actions/request-deploy/action.yml
.github/actions/request-deploy/                 # reviewed helper code and focused tests, if needed
deployment/keys/staging.age.pub                 # public recipient(s) only
deployment/keys/production.age.pub               # public recipient(s) only
<app-repository>/.github/workflows/deploy.yml
<app-repository>/deploy/staging.yml
<app-repository>/deploy/production.yml
docs/runbooks/app-release-and-rollback.md
```

The app workflow and manifests are app-owned; no app source or runtime secret is copied into CentralDevOps. Task summaries belong in `summaries/task-<n>-summary.md` and are written only when their implementation task closes.

## Out of scope

- App image build, digest publication, and provenance attestation (spec 09).
- Central authorization, OIDC verification, registry/ref checks, and replay protection (spec 10).
- Privileged host deployment, health checks, automatic rollback, locks, route activation, and deployment records (spec 11).
- A starter-template product or reusable app workflow (REL-16 is Could and deferred).
- External storage or alternate transport for oversized bundles.
- GitHub Deployments status integration, app schema migrations, and any app-side SSH or host operation.
