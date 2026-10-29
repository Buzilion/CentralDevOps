# Task 4: Digest metadata output

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/spec.md` |
| Depends on | Task 3 |
| Needs | A published digest with a successfully created provenance attestation |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Expose the successful build's immutable image reference in the run summary and a versioned metadata-only artifact.

## Relevant files or references

- Disposable app repository: `.github/workflows/build.yml`
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL-03`)
- `docs/design/naming-and-repository-conventions.md` §4.2
- v5 design §7.1
- Spec 09: Release metadata and run summary

## Proposed approach

1. Validate the registry digest returned by Task 2 as `sha256:<64 lowercase hex>` and construct `image_ref` from the canonical image name.
2. Generate `image-metadata.json` with `schema_version: 1` and the fields specified in the spec. Include only non-secret release metadata.
3. Upload the JSON as a metadata-only artifact after provenance succeeds; do not include the image, build context, logs, or environment files.
4. Write the same `image_ref`, source commit, and convenience tag to the GitHub Actions run summary.
5. Make the summary and artifact agree and clearly distinguish the digest release identity from the non-authoritative tag.

## Acceptance criteria

- The summary contains a complete `ghcr.io/OWNER/IMAGE@sha256:<64 hex>` reference from the actual pushed digest.
- `image-metadata.json` has schema version 1 and includes the repository, workflow ref, source ref, source commit, image name, digest, image ref, convenience tag, run URL, and successful attestation status.
- Summary and artifact values for commit, digest, image ref, and tag match exactly.
- The artifact contains metadata only and is not uploaded after failed tests, publication, or attestation.
- The workflow never presents a tag reference as the deployment identity.

## Source reference

REL-03; NFR-12; v5 §7.1; naming guide §4.2.

## Verify

- Compare the run summary, JSON artifact, GHCR manifest digest, and convenience tag target.
- Validate the JSON shape and confirm the artifact contains no image archive, build context, log, secret, token, or environment file.
- Confirm failed test, push, or attestation runs do not upload successful release metadata.

## Out of scope

Deployment request validation, app deploy workflow, Production provenance enforcement, and image retention policy.
