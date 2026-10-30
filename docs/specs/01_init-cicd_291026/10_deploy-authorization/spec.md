# Spec 10: Deployment Authorization and Preflight

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 10 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review |
| Depends on | `02_dispatch-trust-proof`, `06_registry-and-compose-policy`, and `09_app-build-and-provenance` (each prerequisite checklist must be complete before implementation) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/central-deployment-v1.md` (`DEP`), `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (`SEC`), `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL`), `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (`REG`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§2, 6–7; `docs/design/variables-and-secrets.md` §§2, 4.4, 5.2, 6; `docs/design/naming-and-repository-conventions.md` §§3, 6; v5 design §§4.4, 7.2, 8.1–8.3, 9.2, 12.2–12.3, 16 step 9 |

## What

Implement the CentralDevOps `deploy-app.yml` authorization and preflight path. Before any Environment is selected, the workflow independently verifies the dispatching GitHub App and the app workflow's request-bound OIDC token, derives the app from the verified repository claim, checks the registry, digest, allowed ref, provenance and target inventory, and rejects a replay. Only a successful authorization may reach the validated Staging or Production Environment. After the applicable Environment gate, the workflow opens the sealed bundle in a restricted temporary directory and runs the manifest, Compose and runtime-key checks.

This spec does not connect to a VPS or change a running app. Spec 11 adds deployment execution to the same Environment-bound job; it must not add a second Production approval gate.

## Context

- The privileged workflow runs in CentralDevOps from a ref allowed by the selected Environment: any branch for `Staging` and `release/*` only for `Production`. Apps request deployment by authenticated `workflow_dispatch`; the app never receives an SSH key or connects to a host.
- Spec 02 proves the dispatch actor and OIDC claim contract. Spec 06 owns registry and Compose validation interfaces. Spec 09 owns the image-build provenance contract that this spec verifies.
- Specs 09 and 11 are drafted. This spec may be reviewed now; implementation remains blocked until the checklists for specs 02, 06 and 09 are checked off.
- The OIDC token is short-lived. The `authorize` job must finish before the Environment-bound job waits for Production approval. The later job uses only the validated authorization outputs and must not re-verify the expired token.
- The source run's `run_id` and `run_attempt` identify one request. They are also sent as correlation metadata for spec 12, but must match the signed OIDC claims before they are trusted.
- Pre-approval replay detection uses a read-only Actions run-log claim and per-request serialization. Spec 11 repeats the check against the durable host deployment record before any host mutation.

## Requirements

| ID | Statement | Source |
|---|---|---|
| A-01 | `deploy-app.yml` runs in CentralDevOps and accepts only `workflow_dispatch` with `target_environment`, `image_ref`, `oidc_token`, `sealed_bundle`, `source_run_id` and `source_run_attempt`. The last two are correlation metadata only and must match OIDC claims. No app name, repository, source ref, inventory or host is accepted. | DEP-01, SEC-10; spec 12 |
| A-02 | A request from a CentralDevOps ref not allowed by its requested Environment fails before checkout or Environment selection. `Staging` accepts any branch; `Production` accepts only `release/*`. | DEP-16 |
| A-03 | The trusted `github.actor_id` is independently matched to the immutable dispatch App actor ID captured from the spec 02 proof. Neither actor identity nor app identity is accepted from a dispatch input. | SEC-10; spec 02 |
| A-04 | The `authorize` job has no Environment and reads no repository, organization or Environment secret. It grants only the read permissions required for central files, attestation verification and replay-log scan. | DEP-02, SEC-14 |
| A-05 | The verifier checks the GitHub OIDC signature against the published JWKS; issuer, time claims, audience and required claims; exact source repository; `.github/workflows/deploy.yml`; allowed source ref; source Environment equal to `target_environment`; and exact equality of correlation inputs with signed `run_id` and `run_attempt`. | DEP-02; spec 12 |
| A-06 | The audience is recomputed from the exact request bytes: `centraldevops-deploy:` plus lowercase SHA-256 of `UTF-8(target_environment) || 0x7c || UTF-8(image_ref) || 0x7c || sealed_bundle_bytes`. Base64 transport is strict and is decoded once for this calculation. | DEP-02, REL-08; spec 02 |
| A-07 | The app is derived only by mapping the verified `repository` claim through the registry. `image_ref` must equal that app's registered image repository plus `@sha256:` and exactly 64 lowercase hexadecimal characters. Tags, malformed digests and another app's image fail. | DEP-02, DEP-04 |
| A-08 | The registry's `allowed_refs` authorize the app workflow ref. When `require_attestation` is true, the exact digest must have valid SLSA v1 provenance for the registered app repository and its `build.yml` workflow, including the selected source repository and full source commit in `resolvedDependencies`. Production always requires attestation. | DEP-02, DEP-05, REL-04, REL-15; spec 09 |
| A-09 | The registry entry, requested Environment and Environment inventory agree. Every required placement group resolves to exactly one host in that Environment's inventory; no cross-Environment fallback is allowed. This is a plan check only and makes no host connection. | DEP-06, DEP-07 |
| A-10 | A verified `(repository, run_id, run_attempt)` can be authorized once. Concurrent duplicates and later replays fail before the Environment-bound job starts. A sanitized correlation key is exposed for spec 12 to find the matching central run. | DEP-03; spec 12 |
| A-11 | After authorization and any Production approval, the workflow decrypts the request into a restricted temporary directory, validates the manifest and rendered Compose policy, and verifies that the app runtime file has exactly the declared keys and no reserved platform keys. These checks finish before any host connection. | DEP-10 |
| A-12 | Decrypted content and credentials are masked where appropriate, never printed, emitted as job outputs, uploaded as artifacts or included in summaries, and removed on every job exit path. | DEP-13, SEC-12 |
| A-13 | The Environment-bound job selects only the exact validated `Staging` or `Production` output of `authorize`. Production approval happens after authorization; the preflight-only job added here is extended by spec 11 into the single approved deployment job. | DEP-08; v5 §8.2 |

## Design

### Request contract and jobs

`deploy-app.yml` has one `workflow_dispatch` trigger and exactly these inputs:

| Input | Type | Rule |
|---|---|---|
| `target_environment` | Choice | Exactly `Staging` or `Production` |
| `image_ref` | String | Full GHCR digest reference; revalidated against the registry |
| `oidc_token` | String | Request-bound JWT; never printed or output |
| `sealed_bundle` | String | Canonical base64 age ciphertext for at most 40 KiB of ciphertext; never printed or output |
| `source_run_id` | String | Positive decimal; correlation only and must equal signed `run_id` |
| `source_run_attempt` | String | Positive decimal; correlation only and must equal signed `run_attempt` |

Do not add `app`, `repository`, `ref`, `host`, `inventory`, or generic metadata inputs. The workflow checks the CentralDevOps ref and event actor from trusted GitHub context. The decimal `github.actor_id` captured from the completed spec 02 proof is stored as reviewed, non-secret configuration under `deployment/config/`; do not guess an account name or store the App private key in CentralDevOps.

The workflow has top-level `permissions: {}` and explicit least-privilege permissions per job. Third-party actions are pinned to reviewed 40-character SHAs, checkout disables persisted credentials, and untrusted inputs reach scripts through environment variables rather than shell interpolation.

1. **`reject-disallowed-environment-ref`** runs only when the selected Environment does not permit `github.ref`: `Staging` permits any branch, while `Production` permits only branches matching `release/*`. It has no permissions, checkout, Environment or secrets and exits nonzero with a static check identifier, so an invalid Environment/ref pair cannot appear successful because every job was skipped.
2. **`derive-request-key`** runs only for an Environment/ref combination permitted by that policy and has no Environment, secret or permissions. It decodes only enough of the untrusted JWT payload to calculate a bounded SHA-256 key from `repository`, `run_id` and `run_attempt`. This value is only a correlation/lock key; it is never trusted for authorization. Malformed tokens get a deterministic hash fallback. It emits only a fixed-length hexadecimal value as `REQUEST-CORRELATION-V1:<hash>` so spec 12 can locate even a request rejected by `authorize`.
3. **`authorize`** runs only for an Environment/ref combination permitted by that policy, has no Environment, and verifies the event actor, JWT, correlation inputs, registry, digest, ref, provenance, placement and replay state. It re-computes the lock key from verified claims and requires an exact match. Its outputs are an allowlisted plan only: app slug, validated Environment, image digest, source run ID/attempt/SHA, registry path and correlation key. It never outputs the JWT, bundle, runtime values or a complete event payload.
4. **`deploy`** depends on successful authorization and sets `environment` only from `needs.authorize.outputs.environment`. In this spec it performs preflight only; it has no SSH connection or host mutation. A Production request waits at this job, after the short-lived token has already been checked. The age key is read only after the Environment gate.

The job-level replay concurrency group is derived from the request key, uses `queue: max` and `cancel-in-progress: false`, and serializes duplicate attempts rather than allowing them to overlap or silently replacing a pending attempt. Queue overflow is a failed request, never authorization. A dispatch whose ref is not permitted by its requested Environment fails without starting either privileged job. The app-side dispatcher selects a CentralDevOps ref allowed by the requested Environment; it does not accept a caller-supplied CentralDevOps ref.

### OIDC authorization

`deployment/tools/verify-oidc.py` uses the GitHub-published JWKS at `https://token.actions.githubusercontent.com/.well-known/jwks` and fails closed on network, key, parsing or signature errors. It accepts only the supported signing algorithm and matching `kid`, validates the issuer and time claims with a small documented clock-skew allowance, and requires the claims used below. Never decode-only trust a claim; the pre-auth decode exists only to serialize duplicate work.

After signature verification, the script:

1. Strictly decodes the base64 bundle transport once and enforces the request-size limit. It does not trim whitespace, normalize bytes or decode nested base64.
2. Recomputes the audience from the exact bytes above; no newline or JSON serialization is introduced.
3. Maps the verified `repository` claim to exactly one registry app. The app slug and registry path come from that entry, never from an input or a path assembled from untrusted repository text.
4. Requires `job_workflow_ref` to identify that repository's `.github/workflows/deploy.yml` at the exact verified `ref`, requires the ref in that registry entry's `allowed_refs`, and requires the OIDC `environment` to equal the request's `target_environment`.
5. Requires `source_run_id` and `source_run_attempt` to equal the verified `run_id` and `run_attempt` exactly. It also requires valid positive-decimal claims and a valid source commit SHA for the authorization plan and replay key.

The dispatch App actor check and the OIDC proof are independent. Failure of either rejects the request before the Environment-bound job. Error output uses stable check identifiers and never includes the token, bundle or full claims object.

### Registry, image and provenance preflight

Reuse `deployment/tools/validate-registry.py` from spec 06 for deployment-mode schema and inventory checks; do not implement a second YAML or Ansible inventory parser. Pass only the app derived from the signed repository claim, the validated Environment and the digest input. The validator must confirm the registry path and declared Environment, manifest-domain ownership, inventory match, and exactly one host for each required placement group.

The authorization stage separately enforces `allowed_refs` and the digest grammar. If `require_attestation` is true, verify the exact requested digest with the pinned GitHub CLI attestation verifier against the registered source repository and the app's `.github/workflows/build.yml`. Verify the SLSA v1 predicate's `resolvedDependencies` entry identifies the registered source repository, includes the selected source ref, and has a full `digest.gitCommit` SHA. Do not treat the attestation workflow's `github.sha` alone as the selected source commit, and do not accept provenance from a different repository or workflow. Production registry entries from spec 06 require attestation; Staging may skip it only when its registry policy is false. An unavailable verifier or GitHub read access is a failure, never a skip.

`authorize` returns only the plan fields needed by the next job. It makes no SSH or HTTP request to a target host and does not decrypt the bundle.

### Single-use request protection and correlation

The no-Environment authorizer needs a replay check before approval, while the v5 design also requires the source tuple in the durable host deployment record. Use both layers:

- The `authorize` job is serialized per verified source tuple. A bounded pre-auth decode supplies only the lock key; after signature verification, the authorizer calculates the same key from trusted claims.
- With read-only `actions: read`, `deployment/tools/replay-guard.py` scans the retained attempts of this CentralDevOps `deploy-app.yml` workflow across all refs for the exact marker `REPLAY-CLAIM-V1:<sha256>`. The marker hashes `UTF-8(repository) || 0x7c || ASCII(run_id) || 0x7c || ASCII(run_attempt)` and contains no raw source identity.
- Only after all authorization checks pass does the job emit that marker to its own log and sanitized job summary. A later serialized request finds it and fails before the Environment job. Replays with a different Environment, digest or bundle still collide because the source tuple is the one-time identity.
- The earlier `REQUEST-CORRELATION-V1:<sha256>` marker is a locator only and is never counted as a replay claim. It is the value spec 12 computes from its repository and source run context when locating the matching central run through the Actions API, including when authorization fails. The action must match the exact key; it must not guess from time, app, Environment or digest.
- Keep Actions log retention at least 90 days and verify that the scan is complete. Page through the GitHub API and all prior run attempts. If the run list is truncated, an eligible log is unavailable, the API is rate-limited, or retention is insufficient, fail closed; do not substitute Actions cache or workflow concurrency alone for a replay ledger.
- Spec 11's root-owned server deploy command also checks and records the verified source tuple under its server lock before host mutation. This durable record is defense in depth and the deployment-history source; it does not replace the pre-approval check.

### Sealed-bundle preflight

Use the `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` Environment secret only in the Environment-bound `deploy` job, after authorization and any required Production approval. During key rotation the secret may contain one or two age identities; write each to its own restricted temporary identity file and pass all current identities to the pinned age decryptor. The `DEPLOY_SSH_PRIVATE_KEY` is not used by this spec.

The plaintext is a tar archive containing exactly `runtime.env`, `compose.yml`, and the selected `deploy/staging.yml` or `deploy/production.yml`, as shared with spec 12. Reject missing or extra entries, absolute paths, `..`, symlinks, hard links and oversized members. Do not accept identity or Environment metadata from the archive. Keep the sealed bundle at or below the design's 40 KiB operational target and reject an over-limit input.

Decrypt only into a `0700` temporary directory under the runner temp path with `umask 077`; create files with restrictive permissions. Use a pinned `age` release/checksum, no shell `source`, and no `set -x`. Register the age identities and non-empty runtime values for masking using safe command escaping, while still ensuring no command prints them. Run cleanup with a shell trap and an `if: always()` cleanup step; do not upload any part of the temporary directory.

Preflight then:

1. Validates the selected route manifest with spec 06's schema and deployment-mode validator against the already authorized app and Environment.
2. Parses `runtime.env` without evaluating it, rejects duplicate or malformed names, and compares its key set exactly with `manifest.runtime_env.required`. Reject platform-reserved keys (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `IMAGE_REF`, `EDGE_ALIAS`, and every `CENTRALDEVOPS_*` name); `DB_PASSWORD` remains app-owned when declared by the manifest.
3. Runs spec 06's Compose policy against the fully rendered Compose configuration using explicit files and a controlled interpolation environment. Capture diagnostics and report only sanitized rule IDs, service names and field paths; never print rendered JSON or values.
4. Writes a short sanitized preflight result. No host is contacted and no deployment is attempted.

## Deliverables

```text
.github/workflows/deploy-app.yml
deployment/config/deploy-dispatch-app.json       # non-secret actor identity proved by spec 02
deployment/tools/verify-oidc.py
deployment/tools/replay-guard.py
deployment/tools/validate-runtime-env.py
deployment/tools/tests/                            # verifier, replay and runtime-env cases
deployment/tools/tests/fixtures/                    # synthetic JWTs, keys and bundles
deployment/tools/requirements.txt                  # add pinned JWT/crypto dependency if needed
deployment/tools/github-names.json                 # register consumed Environment secret names
```

`deploy-dispatch-app.json` contains only the decimal `actor_id` from the successful spec 02 proof. Add `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` to the name catalog as an Environment secret introduced by this spec. Do not reference the admin SSH key, initial provider password or Vault password from `deploy-app.yml`. The deploy SSH key is consumed by spec 11.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Use the four request fields plus `source_run_id` and `source_run_attempt` as correlation-only metadata; compare both exactly to the signed claims. | Add caller-supplied app identity or trust the correlation fields | Spec 12 needs an exact polling key; only the OIDC claims authorize a request. | Yes |
| D2 | Verify OIDC and registry policy before selecting an Environment; decrypt and run bundle preflight only after the validated Environment is selected. | Verify after approval; trust input Environment | Tokens expire while approval waits and a request must not choose a different host from its approval. | Yes |
| D3 | Use a read-only Actions run-log claim plus per-request concurrency for pre-approval replay rejection, and keep the host record as defense in depth. | Concurrency alone; Actions cache; a new state service | Concurrency alone is not durable. The read-only log claim needs no new credential or service and can be serialized; incomplete history fails closed. | Yes |
| D4 | Use `run_id` and `run_attempt` from the signed app token as the one-time key; include the verified repository to scope the key. | Central workflow run ID or request-supplied UUID | The source run attempt is the authenticated request identity and cannot be changed without invalidating the proof. | Yes |
| D5 | Preserve the selected manifest path in the archive and accept exactly the three files specified by spec 12. | Arbitrary archive paths or extra metadata | A narrow archive contract makes preflight deterministic and avoids path traversal and identity confusion. | Yes |
| D6 | Spec 10's Environment-bound job is preflight-only and spec 11 extends that same job with deployment. | Add a second Environment-bound job in spec 11 | A second Production job could require a second approval and weaken the intended one-approval flow. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| No Environment is selected until both the dispatch actor and signed OIDC request pass. | Inspect the job graph and verify a rejected request never starts the Environment-bound job. |
| The request binds the exact Environment, digest and ciphertext bytes. | Positive fixture recomputes the audience; changing each field or one ciphertext byte fails. |
| Correlation metadata is never an identity proof. | Mismatched source run ID/attempt fields fail against the signed claims. |
| The app identity cannot be supplied by dispatch input or archive metadata. | Negative input/schema fixtures show identity is derived only from the verified repository claim and registry. |
| Duplicate source run attempts are serialized and rejected before approval. | Dispatch two identical requests concurrently; exactly one reaches the authorized output and the second fails before Environment selection. |
| A registry or host mismatch cannot select another Environment's inventory. | Zero, multiple and cross-Environment placement fixtures fail. |
| Runtime values and OIDC/bundle data never appear in logs, outputs, artifacts or summaries. | Canary scan of test run logs and artifacts; review all `GITHUB_OUTPUT` and summary writes. |
| This spec makes no host connection or host mutation. | Review workflow permissions and steps; use only synthetic fixtures and a disposable bundle. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Any dependency checklist is incomplete. | Do not implement or enable the workflow; leave this spec blocked. |
| Central run ref is not permitted by the requested Environment, or dispatch actor is not the proven App identity. | Fail with a stable check ID before checkout of trusted tools or Environment selection. |
| OIDC signature, issuer, time, audience, required claim or correlation field is invalid. | Fail authorization; never print the token or start the Environment-bound job. |
| Registry mapping, allowed ref, digest, provenance, Environment or placement is absent or ambiguous. | Fail closed before approval; do not guess an app, digest or host. |
| Replay history cannot be checked completely. | Fail closed before approval and report the unavailable check; do not skip replay protection. |
| Bundle encoding, decryption, archive, manifest, Compose policy or runtime key set is invalid. | Fail preflight, sanitize diagnostics, remove temporary files and make no host connection. |
| Production approval is denied or remains pending. | The Environment-bound job does not run; the already-completed authorization is not repeated or weakened. |
| An authorized request is denied approval or fails preflight after the replay marker is written. | Treat that source run attempt as consumed; the operator must start a new app deploy run attempt to retry. |
| A test canary appears in logs or artifacts. | Stop acceptance, remove or mask the exposure, retain only sanitized evidence and leave the task unchecked. |

## Testing Strategy

- Unit tests use generated signing keys and synthetic GitHub claims. Cover invalid signatures/keys/algorithms, issuer/time/audience failures, missing claims, wrong repository/workflow/ref/Environment, mismatched source run metadata, altered request bytes and malformed base64. Never store a live JWT.
- Registry and provenance tests cover an unknown repository, disallowed ref, wrong image repository, tags, malformed or uppercase digest, missing required attestation, wrong signer repository/workflow, missing or invalid SLSA `resolvedDependencies` source commit, and registry/inventory Environment mismatch.
- Replay tests cover two concurrent requests with the same verified tuple, a later replay, a new source `run_attempt`, incomplete API pages/logs, an unavailable API and a log-retention violation. A `REQUEST-CORRELATION` marker alone must not count as a replay; only a post-authorization `REPLAY-CLAIM` does. Only one request with the tuple may reach the Environment job.
- Bundle tests cover successful synthetic decryption, invalid ciphertext, unsafe archive members, missing/extra files, invalid manifest, unsafe rendered Compose, missing/extra/duplicate/reserved runtime keys, old/new age-identity overlap and safe cleanup on both success and failure.
- Run workflow lint and the naming/secrets checker. The workflow must never reference `ANSIBLE_SSH_PRIVATE_KEY`, `VPS_INITIAL_ACCESS_PASSWORD` or `ANSIBLE_VAULT_PASSWORD`.
- A live Staging preflight, if required for acceptance, uses a disposable registered test repository and synthetic bundle only. It performs no host connection and uses no app runtime secret. Do not add a production app or contact a VPS for this spec.
- Record sanitized run URLs, central commit, test/tool versions and outcomes in each task summary only when that task closes. Never include a JWT, bundle bytes, runtime values, private key or host address.

## Out of Scope

- Deploying over SSH, host-side execution, locking, health checks, rollback, route activation, smoke tests and deployment records (spec 11).
- The app-side `request-deploy` action, app `deploy.yml`, sealing and polling (spec 12).
- Adding real application registry entries, onboarding apps or Production deployment acceptance (spec 15).
- Changing the dispatch GitHub App permissions, using a PAT, creating another GitHub Environment or weakening branch/approval protection.
- Any production application secret, VPS credential, live host change or deploy-key use.
