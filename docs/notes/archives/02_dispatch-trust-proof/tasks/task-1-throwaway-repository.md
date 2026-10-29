# Task 1: Prepare the throwaway repository

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Every task in `01_foundation-and-access/checklist.md` is complete and its required protections and Environments have been audited |

## Goal

Prepare a disposable app repository and narrowly scoped GitHub App access for the trust proof, without creating any deployment or host credentials.

## Context

The proof depends on the CentralDevOps `main` protections and the `Staging` and `Production` Environments established by spec 01. Spec 01 is not complete yet; do not create test resources until its checklist is fully checked and the dependency is verified.

The GitHub App is installed only on `Buzilion/CentralDevOps` and has only `Actions: read and write` plus the automatically required metadata access. Its credentials may be exposed only to the disposable app repository through selected-repository org secrets. Do not add a PAT, install the App broadly, or create deploy-related secrets.

## Relevant files or references

- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `docs/specs/01_init-cicd_291026/01_foundation-and-access/checklist.md`
- `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` §§4.5, 7.2, 8.1

## Proposed approach

1. Verify the spec 01 checklist is fully complete and confirm the audited CentralDevOps `Staging` Environment and protected `main` branch are available.
2. Create one clearly named throwaway repository under the organization with no production source or sensitive data. Use its `main` branch for the test workflow.
3. Give the repository access to only the dispatch App credentials needed for the test. Verify the App installation remains limited to CentralDevOps and its permissions match SEC-10.
4. Create only the throwaway app's `Staging` Environment required for OIDC claims. Do not add app runtime secrets or variables.
5. Record the exact disposable repository and temporary resources for later cleanup.

If GitHub's plan, repository access, or organization policy prevents selected-repository credential access or the required Environment behavior, stop and report the blocker; do not broaden access to work around it.

## Acceptance criteria

- The disposable repository has no production code and is identifiable as test-only.
- The dispatch App is installed only on CentralDevOps and has only the required Actions permission.
- Only the disposable repository can access any temporary App credentials used by the proof.
- The disposable repository has the required `Staging` Environment and no runtime credentials.
- No PAT, SSH key, age private key, VPS password, GHCR token, or app runtime secret is created.

## Source reference

DEP-20, SEC-10; spec requirements T-01, T-05, T-07.

## Verify

- Review GitHub App permission and installation settings; confirm the only installation repository is CentralDevOps.
- Review org secret repository access; confirm the only selected app repository is the disposable one.
- List the disposable repository's Environments and confirm the required test `Staging` Environment exists.
- Confirm no deployment-related secrets or variables were created in either repository or Environment.

## Out of scope

Writing workflows, verifying OIDC claims, creating production credentials, or deploying to a host.
