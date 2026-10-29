# Task 5: Validate the sealed bundle safely

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/10_deploy-authorization/spec.md` |
| Depends on | Tasks 1–4; spec 06 checklist complete |
| Summary | `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-5-summary.md` (write when the task closes) |

## Goal

After the validated Environment gate, decrypt a synthetic request in a restricted temporary location and complete every local policy check before any host connection.

## Relevant files or references

- `.github/workflows/deploy-app.yml`
- `deployment/tools/validate-runtime-env.py`
- `deployment/tools/validate-registry.py`
- `deployment/scripts/centraldevops-compose-policy`
- `deployment/keys/{staging,production}.age.pub`
- `docs/design/variables-and-secrets.md` §§4.4, 5.2
- `docs/specs/01_init-cicd_291026/06_registry-and-compose-policy/spec.md`
- `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` (archive and key-rotation contract)

## Proposed approach

1. Use `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` only in the Environment-bound job, after authorization and any Production approval. During rotation, support one or two newline-separated identities by writing each to its own restricted file and passing every active identity to the decryptor. Do not reference `DEPLOY_SSH_PRIVATE_KEY`.
2. Strictly decode the original base64 input for decryption, enforce the bundle limit, and use a pinned `age` binary with a verified checksum.
3. Decrypt the tar archive with `umask 077` into a `0700` runner-temp directory. Accept exactly `runtime.env`, `compose.yml` and the selected `deploy/staging.yml` or `deploy/production.yml`; reject traversal, links, extra members and oversized files.
4. Validate the manifest using spec 06, then parse the runtime file without sourcing it. Require an exact key-set match with `runtime_env.required`; reject duplicates, malformed keys and platform-reserved names. `DB_PASSWORD` is app-owned when declared.
5. Run the existing Compose policy with explicit files and controlled interpolation. Capture output and report only sanitized rule IDs and field paths, never rendered configuration or values.
6. Mask age identities and non-empty runtime values with safe workflow-command escaping. Use a cleanup trap and an `if: always()` cleanup step. Never upload the temp directory.
7. Keep this job preflight-only: no SSH, host lookup over the network, Docker operation or host mutation.

## Acceptance criteria

- A synthetic bundle sealed for the selected Environment decrypts; a bundle sealed for the other Environment fails.
- One-identity operation and old/new recipient overlap both pass with their matching test keys.
- Missing/extra archive members, traversal, links, oversized content and invalid ciphertext fail safely.
- Invalid manifest, Compose policy, missing/extra/duplicate runtime keys and reserved names fail before any host connection.
- `DB_PASSWORD` passes only when included in the manifest's required keys; other platform-owned keys never pass from the app bundle.
- Temporary plaintext and key files are removed on success and failure, and a canary value appears in no log, output, artifact or summary.

## Source reference

DEP-10, DEP-13, SEC-12; requirements A-11 and A-12.

## Verify

- Run archive, manifest, runtime-key and Compose policy tests with synthetic values and bundles.
- Run successful and failing preflight with disposable Staging test keys; verify both cleanup paths and key-rotation overlap.
- Inspect job logs and artifacts for canary values and rendered Compose output.

## Out of scope

Live app runtime secrets, SSH keys, server-side Compose execution, Docker operations or any VPS connection.
