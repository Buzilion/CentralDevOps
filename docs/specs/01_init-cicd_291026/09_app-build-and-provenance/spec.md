# Spec 09: App Build and Provenance

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 09 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation gated on completion of spec 01 |
| Depends on | `01_foundation-and-access` (`checklist.md` must be complete before implementation) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` (`NFR-12`, `NFR-15`) |
| Module PRD | `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL-02`, `REL-03`, `REL-04`, `REL-15`) |
| Design | v5 design §§1, 7.1, 9.2, 15.3, 16 step 8; `docs/design/naming-and-repository-conventions.md` §§4.2, 6; `docs/design/variables-and-secrets.md` §6 |

## What

Define and prove the app-side manual `build.yml` pattern: select a source ref, test the exact resolved commit, publish its image to GHCR, attach build provenance to the pushed digest, and report that immutable digest. The digest is the release identity; the `sha-<full-commit>` tag is only a convenience. This spec does not implement deployment or the Production-side attestation gate.

## Context

- Application source, tests, Dockerfile, and app workflows belong to each app repository. CentralDevOps has no app repository or app-side workflow today, so do not add `.github/workflows/build.yml` to CentralDevOps. The durable operator contract will live in `docs/runbooks/app-build-and-provenance.md`; the end-to-end workflow proof uses a disposable app repository.
- Spec 01 establishes the protected CentralDevOps `main` branch, workflow linting, and action-pinning conventions. Do not create the proof repository or publish an image until its checklist is complete.
- Keep the workflow definition ref (`refs/heads/main`) distinct from the operator-selected `source_ref`. Resolve `source_ref` once to a full commit SHA and use that same SHA for tests, image build, metadata, and provenance so a moving branch cannot change the tested source.
- The app workflow derives its GHCR image name from the app repository and must agree with the reviewed registry image in spec 06. No workflow input may choose the image repository or a deployment target.
- The disposable proof uses a synthetic expected image name only; it must not add a production app entry to the CentralDevOps registry.
- Production requires verified provenance (NFR-15). Because the build workflow has no target-Environment input, the standard pattern always attests builds; Staging builds may use the same attested path. Spec 10 owns central verification and rejection of an unattested Production digest.
- The default GitHub SLSA predicate uses the workflow run's OIDC `ref` and `sha`; with `workflow_dispatch`, those may identify `main`, not a separately selected `source_ref`. The attestation must therefore bind the resolver's selected commit explicitly as a source dependency. Spec 10 must verify that dependency as well as the attestation's repository and workflow identity.
- Confirm GitHub Artifact Attestations are supported for the visibility and plan used by the app repositories. Current GitHub guidance supports public repositories on current plans; private or internal repositories require GitHub Enterprise Cloud. Do not change repository visibility to bypass this prerequisite.
- The proof uses synthetic source and no application runtime secrets, SSH keys, deploy credentials, registry pull token, or VPS access. Use the per-run `GITHUB_TOKEN` with job-scoped permissions; do not add a PAT or long-lived credential.

## Requirements

| ID | Statement | Source |
|---|---|---|
| AB-01 | The app's `.github/workflows/build.yml` is manually triggered by `workflow_dispatch` only, with one required `source_ref` input. It does not call or dispatch the deploy workflow. | REL-01, REL-02; v5 §7.1 |
| AB-02 | The reviewed workflow runs from `main`. It resolves the selected `source_ref` once to a full commit SHA; test and publish steps use that exact SHA and record both the supplied ref and resolved commit. | REL-02; v5 §7.1 |
| AB-03 | App tests finish successfully before any image push. A failed test prevents the publish job from running. The test job does not receive package-write, attestation-write, or identity-token permissions. | REL-02; NFR-15; variables and secrets §6 |
| AB-04 | The workflow publishes to the canonical lowercase `ghcr.io/<owner>/<app-slug>` repository matching the CentralDevOps registry, using the app repository's `GITHUB_TOKEN`. It adds `org.opencontainers.image.source`, and publishes `sha-<full-commit>` as a convenience tag. | REL-02, REL-03; v5 §7.1; naming guide §4.2 |
| AB-05 | On successful publication and attestation, the workflow reports the exact pushed digest as `ghcr.io/OWNER/IMAGE@sha256:<64 hex>` in the run summary and in a metadata-only artifact. The tag is never the release identity or a deploy input. | REL-03; v5 §7.1 |
| AB-06 | The workflow creates a SLSA v1 provenance attestation for the pushed digest. Its signed predicate identifies the app repository and build workflow and records the selected `source_ref` and resolved source commit as a Git dependency. Verification against the expected repository and workflow succeeds. | REL-04; v5 §7.1 |
| AB-07 | The standard build path always creates provenance. A failed or missing attestation fails the workflow and cannot produce a successful release summary or metadata artifact. | REL-15; NFR-15 |
| AB-08 | Third-party actions are pinned to reviewed full commit SHAs. No PAT, runtime secret, deployment credential, or registry pull token is available to the build; no secret is passed in a build argument, image layer, log, summary, or artifact. | NFR-12, NFR-15; variables and secrets §6 |

## Design

### Workflow boundary

The workflow lives in the app repository at `.github/workflows/build.yml`. It has only the `workflow_dispatch` trigger and one required string input, `source_ref`. Dispatch the reviewed workflow from `refs/heads/main`; the input independently selects a branch, tag, or commit to build. Do not add `target_environment`, `image_ref`, deploy credentials, or an automatic build-to-deploy transition.

Pass `source_ref` to the checkout action as its `ref` input, not by interpolating it into shell commands. Resolve the checked-out `HEAD` to a full commit SHA and pass that SHA between jobs. Reject a blank or unresolved ref before tests or publication. Record the original input and resolved commit separately.

Derive the image repository from the app repository identity, normalized to lowercase, and compare it with the reviewed CentralDevOps registry value. Do not accept an operator-supplied image name. Give the app workflow only the permissions needed by each job:

| Job | Minimum permission |
|---|---|
| Resolve source | `contents: read` |
| Test | `contents: read` |
| Publish | `contents: read`, `packages: write` |
| Attest | `contents: read`, `id-token: write`, `attestations: write`, `packages: write` |
| Report | No write permission |

Set workflow-level permissions to none and grant permissions at job level. Disable persisted checkout credentials. Pin checkout, build, attestation, and artifact actions to full commit SHAs reviewed under spec 01.

### Build and publication flow

```text
workflow_dispatch(source_ref), workflow definition from main
  -> resolve source_ref once to source_commit
  -> test source_commit with read-only permissions
  -> publish only after tests pass, from the same source_commit
  -> attest the registry digest
  -> report image_ref and upload metadata-only artifact
```

- Keep the app-specific test commands in the app repository. The test job checks out `source_commit`; it receives no secrets and no package-write permission. The publish job depends on successful resolution and tests, then checks out the same SHA.
- Publish with the per-run `GITHUB_TOKEN`; grant `packages: write` only to the publish job. Do not use a PAT. Do not pass credentials, runtime secrets, or private configuration to Docker as build args or build secrets.
- Set `org.opencontainers.image.source` to the app repository URL so GHCR associates the package with its source repository. Use the canonical lowercase image name. Publish the explicit tag `sha-<full source_commit>` and confirm it points to the image produced by this run.
- Capture the digest returned by the successful GHCR push, validate it as `sha256:<64 lowercase hex>`, and form `image_ref` from the canonical image name and that digest. Do not infer the release digest from the tag.
- The attestation job uses the selected `actions/attest` action and the pushed digest as its subject. It does not rebuild the image. Keep the required OIDC and attestation permissions out of the test job. Do not report a successful release if attestation creation fails.
- CentralDevOps verifies provenance during deployment in spec 10. Build acceptance proves the attestation's subject and repository/workflow/commit claims; it does not implement deployment authorization.

### Attestation action and predicate

The v5 design names `actions/attest-build-provenance`. Its current upstream README describes it as a wrapper and recommends `actions/attest` for new implementations. Use the supported `actions/attest` action pinned to a reviewed full commit SHA. For a container, set `subject-name` to the fully qualified image name without a tag, `subject-digest` to the exact push digest, and `push-to-registry: true`. Grant the container attestation job `contents: read`, `id-token: write`, `attestations: write`, and `packages: write`; do not grant `artifact-metadata: write` unless a separate linked-artifact storage requirement is approved.

The default `actions/attest` SLSA predicate is based on GitHub OIDC claims for the workflow run. Since the operator-selected `source_ref` can differ from the workflow definition ref, create a SLSA v1 predicate from the trusted resolver outputs and pass it with the action's `predicate-type` and `predicate-path` inputs. The predicate must:

- Use `https://slsa.dev/provenance/v1` and the GitHub Actions workflow build type.
- Identify the workflow repository, `.github/workflows/build.yml`, and reviewed workflow ref in its workflow/build fields.
- Include the app source repository and selected `source_ref` as a Git dependency in `buildDefinition.resolvedDependencies`, with `digest.gitCommit` equal to the full `source_commit` used by tests and image build.
- Identify the attestation workflow run in `runDetails`; never use the raw input or application-controlled build output as the source-commit value.

The attestation's GitHub-issued identity must independently verify as the expected repository and workflow. Spec 10 must verify both that identity and the `resolvedDependencies` commit; it must not treat the workflow run's `github.sha` alone as proof of the separately selected source commit.

Upstream references:

- [actions/attest README](https://github.com/actions/attest#usage)
- [GitHub guide: attest container images](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations#generating-build-provenance-for-container-images)
- [GitHub provenance predicate implementation](https://github.com/actions/toolkit/blob/main/packages/attest/src/provenance.ts)

### Release metadata and run summary

After publication and attestation succeed, write the full `image_ref` to the GitHub Actions run summary and upload `image-metadata.json` as a metadata-only artifact. Version the JSON contract (`schema_version: 1`) and include:

| Field | Value |
|---|---|
| `repository` | App repository (`owner/repo`) |
| `workflow_ref` | Full reviewed workflow identity, `<owner>/<repo>/.github/workflows/build.yml@refs/heads/main` |
| `source_ref` | Operator-selected ref |
| `source_commit` | Full resolved commit SHA used for tests and image build |
| `image_name` | Canonical lowercase GHCR repository |
| `image_digest` | `sha256:<64 lowercase hex>` returned by the registry push |
| `image_ref` | Full `image_name@image_digest` reference |
| `convenience_tag` | Full GHCR tag ending in `sha-<full source_commit>` |
| `run_url` | URL of the successful build run |
| `attestation_created` | `true` only after the provenance action succeeds |

The summary and artifact must agree on `source_commit`, digest, `image_ref`, and tag. Do not upload a Docker archive, build context, logs, environment files, credentials, or other application data as the metadata artifact. The tag may help an operator locate an image, but only `image_ref` is valid for deployment.

### Provenance policy

Every successful run through this pattern creates an attestation, including builds later used only in Staging. This is the simplest safe contract because the build has no destination-Environment input and cannot know whether an operator will later request Production. A build may not skip attestation or mark an unattested digest as successful. The deployment workflow remains responsible for verifying the attestation against the registry-selected app repository and expected workflow before Production.

## Deliverables

```text
docs/runbooks/app-build-and-provenance.md
docs/design/variables-and-secrets.md              # update the attestation action and permissions
Disposable app repository: .github/workflows/build.yml and synthetic app used for proof
summaries/task-<n>-summary.md                         # written as each task closes
```

The disposable repository and its test GHCR package are removed after acceptance. Do not add an app workflow or a complete starter template to CentralDevOps; the latter remains REL-16 (Could) and is out of scope.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Keep `build.yml` app-owned and validate it in a disposable app repository; retain the durable operator contract in a CentralDevOps runbook. | Add a central build workflow or a full app starter template | Source, tests, and Dockerfile belong to the app; a full starter template is deferred as REL-16. | Yes |
| D2 | Resolve `source_ref` once and use its full commit SHA for tests, publication, metadata, and provenance. | Re-check out a branch independently in each job | A moving ref must not make the tested commit differ from the published image. | Yes |
| D3 | Separate read-only tests from image publication and grant write permissions only to the jobs that need them. | Run tests with package-write permissions in one job | A test failure must not publish, and app test code should not receive package-write or attestation permissions. | Yes |
| D4 | Always attest builds; do not add a Staging/Production selector to `build.yml`. | Allow operators to skip attestation for a Staging-only build | The workflow cannot know the future deployment target; always-attest satisfies the Production requirement without another mode. | Yes |
| D5 | Use the current `actions/attest` action with a SLSA v1 predicate that explicitly records the selected source commit. | Use the legacy `actions/attest-build-provenance` wrapper or rely on default OIDC `sha` alone | Upstream recommends `actions/attest` for new implementations, and default OIDC claims identify the workflow run ref, which can differ from the input `source_ref`. | Yes |
| D6 | Treat the registry digest as release identity; keep `sha-<full-commit>` as a non-authoritative convenience tag. | Deploy by tag or make the tag the artifact identity | Tags can move; the digest is immutable and is the contract required by REL-03. | Yes |
| D7 | Use a disposable repository and remove its repository and package after proof. | Use an existing app and leave test resources in place | The proof needs a real GHCR push and attestation without relying on production source or credentials. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| Build and deploy remain separate manual operations. | Workflow has only `workflow_dispatch`; inspect that it does not call or dispatch `deploy.yml`. |
| Tests and published image use the same resolved source commit. | Compare the test checkout, publish checkout, metadata, and attestation commit. |
| A failing test cannot push an image. | Force the synthetic test to fail and confirm the publish job is skipped and no package/tag is created for that commit. |
| The `image_ref` identifies the pushed GHCR manifest, and the convenience tag points to that same digest for this run. | Pull or inspect both references and compare digests. |
| A successful build has a verifiable attestation for the exact digest and expected app workflow, with the selected commit in `buildDefinition.resolvedDependencies`. | Run `gh attestation verify` constrained to the disposable repository and `.github/workflows/build.yml`; inspect the SLSA predicate. |
| Production never relies on an unattested digest. | Confirm every successful standard build is attested; spec 10 verifies and rejects missing or invalid provenance. |
| The metadata artifact contains only release metadata. | Inspect artifact contents and run logs; confirm there is no image archive, secret, token, or environment file. |
| No server or deployment credential reaches the app build. | Review workflow permissions, secret references, action inputs, and proof-repository settings. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Spec 01 checklist is incomplete or protected-main/action-pin prerequisites are not verified. | Do not create the proof repository or publish an image; report the missing prerequisite. |
| The GitHub plan does not support Artifact Attestations for the intended repository visibility. | Keep the spec blocked and report the plan limitation; do not make the proof repository public or substitute an unreviewed signing service. |
| The workflow is dispatched from a ref other than `refs/heads/main`. | Reject before any package-write job starts. |
| `source_ref` is blank or cannot be resolved. | Fail before tests and publication; identify the ref input without echoing any credential. |
| The resolved SHA differs between stages or checkout fails. | Stop the workflow; do not publish or create metadata. |
| App tests fail. | Fail the run and skip publication, attestation, and successful release reporting. |
| The image name does not match the reviewed registry or the push fails. | Fail without substituting another repository, PAT, or mutable fallback tag. |
| The pushed digest is malformed or the convenience tag resolves to another digest. | Fail without presenting a successful `image_ref`. |
| Attestation creation fails or does not bind the expected digest, repository, workflow, and resolved source commit. | Fail the run; do not upload successful release metadata or claim the digest is Production-ready. |
| A test-only credential, runtime secret, or deploy credential is exposed. | Stop, revoke/remove the test-only value, preserve sanitized evidence, and do not continue acceptance. |
| The temporary repository or GHCR package cannot be removed after acceptance. | Record the exact remaining resource, revoke any access, and keep the acceptance task incomplete until cleanup is verified. |

## Testing Strategy

- **Static workflow checks:** lint the proof workflow; check trigger and input shape, action SHA pins, job permissions, branch gate, and absence of secret or deployment inputs.
- **Successful build:** dispatch from `main` with a valid `source_ref`; verify that tests and publication use the same commit, GHCR contains the canonical image and `sha-<full-commit>` tag, and the returned digest is pullable.
- **Test failure:** run a synthetic commit whose test fails; verify publication, attestation, summary, and metadata upload do not report success and no GHCR image/tag is created for that commit.
- **Digest and metadata:** compare the registry digest, `image_ref`, tag target, run summary, and JSON artifact. Inspect the artifact to confirm metadata-only contents.
- **Provenance:** run `gh attestation verify` against the OCI digest with the expected repository and workflow; inspect the SLSA v1 `resolvedDependencies` entry and confirm its `gitCommit` is the tested source SHA. Verify that a different digest, repository, workflow, or source SHA is not accepted.
- **Package association and secret audit:** confirm the GHCR package links to the app repository through `org.opencontainers.image.source`; inspect workflow permissions, logs, summaries, and artifacts for credentials or runtime values.
- **Cleanup:** delete the named disposable repository and its test package, then verify both are absent. Record only sanitized run URLs, tested commit, dates, outcomes, and cleanup evidence in task summaries.

## Out of Scope

- Central `deploy-app.yml`, Production-side provenance enforcement, OIDC authorization, and registry lookup (spec 10).
- App `deploy.yml`, `request-deploy`, runtime-secret sealing, rollback, and the full operator build-to-Production flow (spec 12).
- A reusable build action or complete starter template containing both app workflows, Compose, and route manifests (REL-16).
- Real application source, production GHCR packages, runtime secrets, server credentials, VPS access, or deployment.
- CentralDevOps-owned test commands, Dockerfiles, image retention policy, or cleanup policy for production images.
