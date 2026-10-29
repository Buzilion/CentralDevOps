# Task 2: Implement the production OIDC verifier

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/10_deploy-authorization/spec.md` |
| Depends on | Task 1 |
| Summary | `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-2-summary.md` (write when the task closes) |

## Goal

Verify the app-issued OIDC token and prove it binds the exact dispatch Environment, digest and sealed-bundle bytes.

## Relevant files or references

- `deployment/tools/verify-oidc.py`
- `deployment/tools/requirements.txt`
- `deployment/tools/tests/test_verify_oidc.py`
- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/spec.md`

## Proposed approach

1. Use a reviewed, pinned JWT/crypto dependency and fetch GitHub signing keys only from the published OIDC JWKS endpoint with normal TLS verification and bounded timeouts.
2. Verify the signature, supported algorithm and `kid`; require the GitHub issuer, valid `exp`/`nbf`/`iat` with a small documented clock skew, and all source identity claims.
3. Strictly decode the base64 ciphertext once in this verifier. Recompute the audience from UTF-8 `target_environment`, a literal `|`, UTF-8 `image_ref`, a literal `|`, and the exact decoded ciphertext bytes.
4. Require the exact repository, `.github/workflows/deploy.yml`, allowed source ref and matching source Environment after the signature passes.
5. Require `source_run_id` and `source_run_attempt` to equal the signed `run_id` and `run_attempt` exactly. Treat these dispatch fields as correlation only, never as identity.
6. Return only an allowlisted set of non-sensitive verified values. Never write the JWT, bundle, full claims or authorization input to stdout, a file artifact or `GITHUB_OUTPUT`.
7. Build unit tests from generated keys and synthetic claims; mock JWKS retrieval. Do not store live GitHub JWTs or use them as fixtures.

## Acceptance criteria

- A correctly signed synthetic token with the exact request audience and matching correlation fields passes.
- Invalid signature, unknown key, unsupported algorithm, wrong issuer, expired/not-yet-valid token, missing claim and future timestamp fail closed.
- Wrong repository, workflow, ref, Environment, source run metadata, image reference or a single changed bundle byte fails.
- Noncanonical/malformed base64 and an over-size request fail without decoding into an artifact or printing input data.
- The verifier returns stable, sanitized error identifiers and never returns the token or ciphertext.

## Source reference

DEP-02, SEC-14, REL-08; requirements A-05 and A-06.

## Verify

- Run the focused verifier unit tests with generated signing keys.
- Search test output and failure messages for synthetic token markers and bundle contents.
- Run the repository Python test suite and required workflow lint.

## Out of scope

Registry policy, provenance verification, replay storage, decrypting the bundle or deployment.
