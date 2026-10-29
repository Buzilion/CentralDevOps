# Task 2: Implement the app-side dispatch proof

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Task 1 |

## Goal

Add a minimal workflow to the disposable repository that creates a synthetic request, obtains a request-bound OIDC token, and dispatches the CentralDevOps proof workflow using the dispatch-only GitHub App.

## Context

This workflow proves the real cross-repository request path. It must not handle real app data or secrets, and must not connect to a VPS. Keep its permissions to `contents: read` and `id-token: write`; all third-party actions must be pinned to reviewed commit SHAs in accordance with spec 01.

## Relevant files or references

- Disposable repository: `.github/workflows/deploy.yml`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `docs/specs/01_init-cicd_291026/01_foundation-and-access/spec.md` (workflow security requirements)
- `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` §§7.2, 8.1

## Proposed approach

1. Add a manually triggered workflow on `main` with the app-side `Staging` Environment and only the permissions described above.
2. Use fixed, non-secret synthetic values for `target_environment`, a valid-format test image digest, and bundle bytes. Compute the audience exactly from the values and bytes sent: `centraldevops-deploy:` plus SHA-256 of `environment | image_ref | bundle`.
3. Request an OIDC token for that audience. Keep the token in memory or a protected step output only as needed for dispatch; never echo it, mask output, upload it, or persist it as an artifact.
4. Create an installation token using the selected-repository App credentials and dispatch the CentralDevOps proof workflow with the target Environment, image reference, token, and synthetic bundle.
5. Pin every action and pass all untrusted values to commands through environment variables or protected inputs, never direct expression interpolation into shell.
6. Emit only a run URL and non-sensitive success/failure status.

## Acceptance criteria

- The workflow triggers manually from the disposable repository's reviewed `main` branch and uses its `Staging` Environment.
- The OIDC audience is computed from exactly the dispatched Environment, digest, and bundle.
- The GitHub App installation token successfully dispatches the CentralDevOps proof workflow.
- The workflow has no deploy, SSH, age, registry, or runtime credentials, and cannot connect to a VPS.
- Logs and artifacts contain no OIDC token, installation token, or bundle contents.

## Source reference

DEP-20, SEC-10, SEC-14; spec requirements T-01, T-02, T-07.

## Verify

- Run the workflow manually from `main` and confirm CentralDevOps receives a dispatch on its `main` branch.
- Review the workflow permissions and action SHA pins.
- Inspect the source and central workflow logs and artifacts for token or bundle leakage.
- Confirm the audience input matches an independent recomputation from the three synthetic request values.

## Out of scope

Production `request-deploy` action, production app workflows, runtime secrets, or deployment behavior.
