# Task 2: Onboarding contract and guide

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | Task 1 |
| Needs | Accepted registry, app workflow, database, secret, and Environment contracts from specs 06, 08-12 |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Create the operator and developer onboarding guide with a complete app contract and an ordered, repeatable onboarding path.

## Relevant files or references

- Create `docs/runbooks/app-onboarding.md`
- `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (REG-09 to REG-11)
- `docs/prd/01_init-cicd_291026/database-v1.md` (DB-05, DB-06)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-01, SEC-08 to SEC-10, SEC-15, SEC-18)
- v5 design §§7.1-7.2, 9.1-9.3, 11.3, 12.3, 15.2-15.3
- `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md`

## Proposed approach

1. Document the reviewed CentralDevOps registry PR, capacity check, DNS setup, app repository files, the two Environments, scoped `APP_*` configuration, and dispatch App credentials.
2. Document the supported sequence: build an immutable digest, deploy to Staging, verify, then request Production through CentralDevOps after the go-live gates pass.
3. Define app-owned and platform-owned inputs. Include the Dockerfile, Compose file, per-Environment manifest, health endpoint, resource limits, stateless-container requirement, durable-data locations, and runtime environment-variable contract.
4. State that secrets must not be placed in image layers, build arguments, labels, committed Compose files, workflow inputs, artifacts, or logs. State that app repositories never receive platform SSH keys, the registry pull token, or the central decryption key.
5. Document the `DB_*` ownership contract and require app-owned migrations to remain backward compatible. CentralDevOps runs only an explicitly declared and validated optional release command; it never authors or independently runs schema migrations.
6. Include a checklist that records the effective container user for each app, non-root status where supported, any exception and its reason, plus sanitized Staging and Production evidence references.
7. Include the chosen Production reviewer handoff from Task 1 and make clear that the app Production Environment has no reviewer by default.

## Acceptance criteria

- The guide enables a second app to follow the same CentralDevOps workflows without central workflow edits.
- All REG-10 contract items and the DB-06 migration ownership/backward-compatibility rule are present.
- The onboarding checklist records the container user and a reason for any non-root exception.
- The guide clearly distinguishes app-owned configuration/secrets from CentralDevOps-owned placement, deployment credentials, and approval.
- The guide makes Production conditional on all five recorded go-live gates.
- No real secret, credential, app runtime value, or unapproved host detail is included.

## Source reference

REG-09, REG-10, REG-11; DB-05, DB-06; SEC-01, SEC-08 to SEC-10, SEC-15, SEC-18; v5 §§7.1-7.2, 9.1-9.3, 11.3, 12.3, 15.2-15.3.

## Verify

- Walk through the guide against the final spec 06 registry/manifest schemas and specs 09-12 workflow interfaces.
- Review the migration and health-check wording with the shared-database and deployment runbooks.
- Confirm every prerequisite, ownership boundary, and evidence field can be followed without inventing a CentralDevOps workflow change.

## Out of scope

Creating an app starter-template product, changing central workflows, implementing registry/policy logic, or authoring app-specific code.
