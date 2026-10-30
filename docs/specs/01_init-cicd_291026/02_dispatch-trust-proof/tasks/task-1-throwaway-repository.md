# Task 1: Prepare the throwaway repository

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md` |
| Depends on | Every task in `01_foundation-and-access/checklist.md` is complete and its required protections and Environments have been audited |
| Summary | `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/summaries/task-1-summary.md` (write when the task closes) |

## Goal

Prepare a disposable app repository and narrowly scoped GitHub App access for the trust proof, without creating any deployment or host credentials.

## Context

The proof depends on the CentralDevOps `main` and `release/*` protections and the `Staging` and `Production` Environments established by spec 01. Do not create test resources until spec 01's checklist is fully complete and the dependency is verified.

The dispatch GitHub App is installed only on `Buzilion/CentralDevOps` and has only `Actions: read and write` plus automatically required metadata access. Any temporary App credentials are accessible only to the disposable app repository through selected-repository org secrets. Do not add a PAT, install the App broadly, or create deploy-related secrets.

## Relevant files or references

- `docs/specs/01_init-cicd_291026/02_dispatch-trust-proof/spec.md`
- `docs/specs/01_init-cicd_291026/01_foundation-and-access/checklist.md`
- `docs/design/variables-and-secrets.md` §§2, 5.3
- `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` §§4.5, 7.2, 8.1

## Proposed approach

1. Verify the spec 01 checklist is fully complete and confirm the audited CentralDevOps `Staging` and `Production` Environments and protected `main` and `release/*` branches are available.
2. Create one clearly named throwaway repository under the organization, containing no production source or sensitive data. Use its reviewed `main` branch for the test workflow.
3. Configure only the `Staging` and `Production` Environments in the throwaway repository. Add no secrets. Leave app-side `Production` without required reviewers and restrict its deployment refs to `main` and any explicitly approved release refs.
4. Give only the throwaway repository access to any temporary dispatch App credentials. Verify the App installation remains limited to CentralDevOps and its permissions match SEC-10.
5. Record the exact disposable repository and temporary resource names for later cleanup. Do not record credential values.

If GitHub's plan, repository access, or organization policy prevents selected-repository credential access or the required Environment behavior, stop and report the blocker; do not broaden access to work around it.

## Acceptance criteria

- The disposable repository has no production code and is identifiable as test-only.
- It has only the required `Staging` and `Production` Environments, with no secrets; app-side `Production` has no required reviewers and is restricted to the approved refs.
- The dispatch App is installed only on CentralDevOps and has only the required Actions permission.
- Only the disposable repository can access any temporary App credentials used by the proof.
- No PAT, SSH key, age private key, VPS password, GHCR token, or app runtime secret is created.

## Source reference

DEP-20, SEC-10, SEC-15; spec requirements T-01, T-07, T-08.

## Verify

- Review GitHub App permission and installation settings; confirm the only installation repository is CentralDevOps.
- Review org secret repository access; confirm the only selected app repository is the disposable one.
- List the disposable repository's Environments and confirm only `Staging` and `Production` are present and neither contains secrets.
- Audit the app `Production` deployment branch rules and confirm no required reviewers are configured.
- Confirm no deployment-related secrets or variables were created in either repository or Environment.

## Out of scope

Writing workflows, verifying OIDC claims, creating production credentials, or deploying to a host.
