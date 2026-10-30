# Task 2: Implement the app-side dispatch proof

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Task 1 |
| Summary | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/summaries/task-2-summary.md` (write when the task closes) |

## Goal

Add a minimal workflow to the disposable repository that creates a synthetic request, obtains a request-bound OIDC token, and dispatches the CentralDevOps proof workflow using the dispatch-only GitHub App.

## Context

This workflow proves the real cross-repository request path. It must not handle real app data or secrets, and must not connect to a VPS. Keep its permissions to `contents: read` and `id-token: write`; all third-party actions must be pinned to reviewed commit SHAs in accordance with spec 01.

## Relevant files or references

- Disposable repository: `.github/workflows/deploy.yml`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` (workflow security requirements)
- `docs/design/variables-and-secrets.md` §5.3
- `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` §§7.2, 8.1

## Proposed approach

1. Add a manually triggered workflow on the throwaway repository's reviewed `main` branch. Run the positive proof in its app-side `Staging` Environment and grant only the permissions described above.
2. Use fixed, non-secret synthetic values for `target_environment`, a valid-format test image digest, and sealed-bundle bytes. Compute the audience using the exact byte sequence in spec T-02; base64-encode the bundle only for dispatch transport.
3. Request an OIDC token for that audience. Mask it before use, keep it in memory where practical, and pass it only to the dispatch request. Never echo it or place it in a step output, job output, artifact, or run summary.
4. Create an installation token using the selected-repository App credentials and dispatch the CentralDevOps proof workflow with `target_environment`, `image_ref`, the OIDC token, and the synthetic bundle. Use a non-main CentralDevOps test ref for the Staging proof; do not send an app-name input.
5. Pin every action and pass all untrusted values to commands through environment variables or protected inputs, never direct expression interpolation into shell.
6. Emit only a run URL and non-sensitive success or failure status.

## Acceptance criteria

- The workflow triggers manually from the disposable repository's reviewed `main` branch and uses its `Staging` Environment.
- The OIDC audience is computed from exactly the dispatched Environment, digest, and sealed-bundle bytes.
- The GitHub App installation token successfully dispatches the CentralDevOps proof workflow from a non-main Staging-allowed ref.
- The workflow has no deploy, SSH, age, registry, or runtime credentials, and cannot connect to a VPS.
- Logs and artifacts contain no OIDC token, installation token, or bundle contents.

## Source reference

DEP-20, SEC-10, SEC-14; spec requirements T-01, T-02, T-07.

## Verify

- Run the app workflow manually from `main` and confirm CentralDevOps receives the Staging dispatch on the selected non-main test branch.
- Review the workflow permissions and action SHA pins.
- Inspect the source and central workflow logs and artifacts for token or bundle leakage.
- Independently recompute the audience from the synthetic Environment, image reference, and exact bundle bytes; confirm it matches the value requested from GitHub.

## Out of scope

Production `request-deploy` action, production app workflows, runtime secrets, or deployment behavior.
