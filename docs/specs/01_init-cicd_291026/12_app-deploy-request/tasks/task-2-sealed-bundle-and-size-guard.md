# Task 2: Sealed bundle and size guard

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` |
| Depends on | Task 1 |
| Needs | Reviewed Staging and Production age public recipients; matching private identities accepted only by the spec 11 CentralDevOps decryptor |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Create the minimal Environment-specific encrypted request bundle without exposing plaintext runtime values or relying on an unreviewed alternate transport.

## Relevant files or references

- `.github/actions/request-deploy/action.yml` and its helper code
- `deployment/keys/staging.age.pub` and `deployment/keys/production.age.pub` (public recipients only)
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-07, REL-12)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-06, SEC-08, SEC-12)
- `docs/design/variables-and-secrets.md` §§4.4, 5.2
- v5 design §§7.2, 15.5

## Proposed approach

1. Build a bundle containing only `runtime.env`, `compose.yml`, and the selected manifest (`Staging` maps to `deploy/staging.yml`; `Production` maps to `deploy/production.yml`). Use fixed member names and reject missing files, unexpected members, or unsafe paths.
2. Create temporary working files under the runner temporary directory with restrictive permissions. Do not place plaintext in the workspace, commit it, upload it, or print it; clean it up on every exit path.
3. Select only the recipient(s) for `target_environment` from the reviewed public key files. Seal for both old and new recipients during the documented rotation overlap, and confirm spec 11's decryptor accepts both corresponding private identities. Never read or package an age private key.
4. Use a pinned, reviewed age implementation. Preserve the exact encrypted byte sequence for the subsequent OIDC audience calculation; do not normalize it or append a newline.
5. Keep the sealed bundle at or below the 40 KiB operational target and measure the encoded request components. Task 3 performs the hard check against the fully serialized dispatch body after the OIDC token is available.
6. On encryption failure, stop before dispatch with a sanitized message. Do not retry by uploading an artifact, external object, URL, or split bundle.
7. Test both successful cleanup and cleanup after an injected encryption/size failure.

## Acceptance criteria

- The sealed bundle has exactly the three specified files and contains the selected Environment's values only.
- The wrong Environment's private key cannot decrypt the bundle; the matching key can, and both matching identities are accepted by the central decryptor during the planned rotation overlap.
- No plaintext runtime value, private key, token, or bundle contents appear in logs, artifacts, action outputs, or committed files.
- Temporary plaintext files are private to the runner account and removed on both success and failure.
- The action measures the bundle and reports only its size; exceeding the 40 KiB target does not bypass the full-request hard cap or trigger another transport.
- The exact sealed bytes are available to Task 3 without transformation for audience hashing.

## Source reference

REL-07, REL-12; SEC-06, SEC-08, SEC-12; v5 §§4.4, 7.2, 15.5.

## Verify

- Decrypt synthetic bundles with the matching and nonmatching Environment keys.
- Exercise dual-recipient encryption with synthetic old/new keys.
- Inspect archive members, file permissions, cleanup, logs, artifacts, and outputs using synthetic canary values.
- Test boundary sizes around 40 KiB and confirm the exact hard dispatch-body cap is applied in Task 3.

## Out of scope

OIDC audience generation, GitHub App token creation, dispatch, central decryption, or host deployment.
