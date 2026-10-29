# Task 3: Authorize registry, digest and provenance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/10_deploy-authorization/spec.md` |
| Depends on | Tasks 1–2; specs 06 and 09 checklists complete |
| Summary | `docs/specs/01_init-cicd_291026/10_deploy-authorization/summaries/task-3-summary.md` (write when the task closes) |

## Goal

Map verified source identity to one registered app and prove the requested image and target plan are allowed before any Environment is selected.

## Relevant files or references

- `deployment/tools/verify-oidc.py`
- `deployment/tools/validate-registry.py` and its deployment-mode interface from spec 06
- `deployment/schemas/registry.schema.json`
- `deployment/tools/tests/`
- `docs/prd/01_init-cicd_291026/central-deployment-v1.md` DEP-02, DEP-04 to DEP-07
- `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/spec.md`

## Proposed approach

1. Map the verified OIDC `repository` to exactly one registry record. Derive the app slug and registry path from that record; never build a path from untrusted request text.
2. Validate the registry entry for the exact target Environment and run spec 06's validator with the verified app, Environment and `image_ref`.
3. Enforce `allowed_refs`, exact `.github/workflows/deploy.yml` identity and the `ghcr.io/<registered image>@sha256:<64 lowercase hex>` form. Reject tags, another repository and malformed digests.
4. When `require_attestation` is true, use the pinned GitHub CLI verifier against the registered app repository and `.github/workflows/build.yml`.
5. Verify the attested subject is the requested digest and the signed SLSA v1 predicate includes the registered source repository, selected `source_ref` and a full `digest.gitCommit` in `buildDefinition.resolvedDependencies`. Do not substitute the attestation workflow's `github.sha`.
6. Resolve every required placement group against the same Environment inventory; require exactly one host per group. Return only the non-sensitive plan fields required by the next job.
7. Do not connect to the target or introduce a second Ansible inventory parser. Record any interface mismatch with spec 06 or 09 as a blocker rather than adding a silent fallback.

## Acceptance criteria

- Unknown or ambiguous repository mappings, missing registry records and Environment/path mismatches fail before Environment selection.
- Ref outside `allowed_refs`, app/workflow mismatch, cross-app image, tag and malformed digest each fail.
- Production (and any entry with `require_attestation: true`) rejects missing or invalid provenance for the exact image digest, expected build workflow, registered source repository, selected source ref and full resolved source commit.
- Zero-host, multi-host and cross-Environment placement fixtures fail; exactly one matching host per required group passes.
- No host address, complete registry record or secret is printed or placed in workflow outputs.

## Source reference

DEP-02, DEP-04, DEP-05, DEP-06, DEP-07; REG-01 to REG-04; spec 09 AB-06; requirements A-07 to A-09.

## Verify

- Run deployment-mode validator tests using synthetic registry and inventory fixtures.
- Test attestation verification with valid and invalid fixture provenance supported by spec 09.
- Confirm errors fail before the Environment-bound job and reveal no private input.

## Out of scope

Adding real app registry records, connecting to a host, deploying an image, or implementing the spec 09 build workflow.
