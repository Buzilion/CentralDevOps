# Task 2: Test-gated GHCR publish

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/spec.md` |
| Depends on | Task 1 |
| Needs | Disposable app repository from Task 1; GITHUB_TOKEN-only package publishing; no deployment credentials or production registry entry |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Run app tests against the resolved commit and publish its canonical GHCR image only after the tests pass.

## Relevant files or references

- Disposable app repository: `.github/workflows/build.yml`, synthetic test command, and Dockerfile
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL-02`, `REL-03`)
- `docs/design/naming-and-repository-conventions.md` §4.2
- `docs/design/variables-and-secrets.md` §6
- Spec 09: Build and publication flow

## Proposed approach

1. Add a test job that checks out the resolved SHA from Task 1 and runs the synthetic app's tests with `contents: read` only.
2. Add a publish job that depends on successful source resolution and tests, then checks out the same SHA.
3. Derive and lowercase the GHCR image name from the app repository; confirm it matches the intended CentralDevOps registry value. Do not accept it as an input.
4. Publish using the per-run `GITHUB_TOKEN`; grant `packages: write` only to the publish job. Do not use a PAT or pass credentials/secrets to Docker.
5. Set `org.opencontainers.image.source` to the app repository URL and publish `sha-<full source_commit>` as the convenience tag.
6. Capture the registry digest from the push as a non-secret job output for Task 3; do not construct it from the tag.

## Acceptance criteria

- Test and publish jobs check out the identical full commit SHA.
- The publish job cannot start unless the test job succeeds.
- The test job has no `packages: write`, `attestations: write`, or `id-token: write` permission.
- A failing test causes publication to be skipped and creates no package/tag for that commit.
- A successful run pushes to the canonical lowercase GHCR repository and publishes the full-commit convenience tag.
- No PAT, runtime secret, deploy credential, or GHCR pull token is used or exposed to the build.

## Source reference

REL-02, REL-03; NFR-12, NFR-15; variables and secrets §6; v5 §7.1; naming guide §4.2.

## Verify

- Run a successful build from a synthetic commit and confirm the GHCR package and `sha-<full-commit>` tag are created.
- Run a failing-test commit with a unique SHA and confirm its publish job is skipped and no package/tag is created for that commit.
- Inspect the job permission blocks, source label, action pins, and build inputs for credential leakage.

## Out of scope

Attestation generation, digest reporting, metadata artifact, operator runbook, and real application publishing.
