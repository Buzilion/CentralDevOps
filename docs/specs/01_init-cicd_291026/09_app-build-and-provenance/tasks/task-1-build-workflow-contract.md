# Task 1: Build workflow contract

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/09_app-build-and-provenance/spec.md` |
| Depends on | Spec-level gate: spec 01 checklist complete |
| Needs | A dedicated disposable app repository with synthetic source and no credentials |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Establish the app-side `build.yml` contract and implement its trigger, input, and source-resolution boundary in the disposable repository.

## Relevant files or references

- Disposable app repository: `.github/workflows/build.yml`
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (`REL-01`, `REL-02`)
- `docs/design/naming-and-repository-conventions.md` §6
- v5 design §§7.1, 16 step 8
- Spec 09: Workflow boundary and Decisions D1-D3

## Proposed approach

1. Confirm spec 01's checklist is complete and Artifact Attestations are supported for the intended repository visibility before creating the disposable repository. Do not change visibility to bypass a plan limitation.
2. Create a clearly named app proof repository containing only synthetic source, a minimal Dockerfile, and a test command. Do not add runtime secrets, server credentials, or production app data.
3. Add `.github/workflows/build.yml` with `workflow_dispatch` only and one required string input, `source_ref`. Do not add a deploy trigger or target-Environment input.
4. Require the workflow definition ref to be `refs/heads/main`; resolve the supplied `source_ref` once to a full commit SHA and expose the original ref and resolved SHA as non-secret job outputs.
5. Pass the input to checkout through its `ref` input; do not interpolate it into a shell command. Pin every third-party action to a reviewed full commit SHA.
6. Set workflow-level permissions to none and give the resolve job only `contents: read`.

## Acceptance criteria

- The only trigger is `workflow_dispatch`, and the only input is required `source_ref`.
- Dispatching the workflow from a ref other than `refs/heads/main` fails before a job with package-write permission can start.
- A valid branch, tag, or commit input resolves to one full commit SHA; an empty or unresolved value fails before tests or publication.
- The raw input is not interpolated into shell code, and the workflow does not start deployment or accept an image name.
- Every third-party action in the proof workflow is pinned to a full commit SHA.

## Source reference

REL-01, REL-02; NFR-15; v5 §§7.1, 16 step 8.

## Verify

- Run the repository's workflow linter against the proof workflow.
- Review the parsed trigger, input, workflow-ref gate, action references, and permission block.
- Dispatch a positive run from `main` and a negative run from another ref; confirm the negative run cannot reach a permissioned publish job.

## Out of scope

GHCR image publication, provenance generation, summary/artifact generation, and production app onboarding.
