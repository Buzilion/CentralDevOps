# Task 3: Build provenance attestation

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/spec.md` |
| Depends on | Task 2 |
| Needs | A successfully pushed disposable GHCR image, its registry digest, and an account plan supporting Artifact Attestations for the proof repository's visibility |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Create a verifiable SLSA v1 provenance attestation for the exact GHCR digest published by Task 2, including the separately selected source commit.

## Relevant files or references

- Disposable app repository: `.github/workflows/build.yml`
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL-04`, `REL-15`)
- `docs/design/variables-and-secrets.md` §6
- v5 design §§7.1, 9.2
- [Current `actions/attest` usage](https://github.com/actions/attest#usage)
- Spec 09: Attestation action and predicate, Provenance policy, and Decisions D4-D5

## Proposed approach

1. Add a separate attestation job that depends on successful publication and consumes the digest output from Task 2; do not rebuild or identify the subject by tag.
2. Use the supported `actions/attest` action pinned to a reviewed full commit SHA; supply the canonical image name without a tag, the exact digest, and `push-to-registry: true`.
3. Generate a SLSA v1 predicate from trusted workflow context and resolver outputs. Put the workflow identity in `buildDefinition.externalParameters.workflow` and `runDetails.builder.id`; put the selected source repository/ref/full commit in `buildDefinition.resolvedDependencies`. Do not treat the default workflow-run `github.sha` as the selected source commit.
4. Grant `contents: read`, `id-token: write`, `attestations: write`, and `packages: write` only to the attestation job. Do not grant `artifact-metadata: write` unless linked-artifact storage is separately approved.
5. Update `docs/design/variables-and-secrets.md` §6 to name `actions/attest` and document the container attestation permissions.
6. Keep attestation mandatory for every successful build; do not introduce a Staging-only skip option.

## Acceptance criteria

- A successfully published image receives an attestation whose subject is the same digest returned by the GHCR push.
- The signed SLSA v1 predicate identifies the expected repository and build workflow and includes the resolved source SHA as the Git dependency digest.
- `gh attestation verify` succeeds when constrained to the expected repository and workflow.
- Verification against a different subject, repository, or workflow does not accept the proof; predicate inspection rejects a different source SHA.
- If attestation creation fails, the workflow fails and does not report a successful release or upload its success metadata.
- Test job permissions remain read-only; OIDC and attestation permissions are not granted workflow-wide.
- The proof repository visibility matches the intended app-repository visibility and the account plan supports attestations; do not make the repository public to work around a plan limitation.

## Source reference

REL-04, REL-15; NFR-15; v5 §7.1; variables and secrets §6.

## Verify

- Verify the attestation for the pushed digest using GitHub CLI and inspect the non-secret repository, workflow, and commit claims.
- Inspect the SLSA v1 predicate's `buildDefinition.resolvedDependencies`; confirm `digest.gitCommit` equals the commit tested and published.
- Try verification with a different expected subject and repository/workflow; confirm it fails.
- Exercise an attestation failure in the proof workflow and confirm the run cannot report success.

## Out of scope

Central deployment-time verification, registry policy, Production authorization, digest summary, and metadata artifact.
