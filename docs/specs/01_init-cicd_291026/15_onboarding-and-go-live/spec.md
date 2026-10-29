# Spec 15: Onboarding and Go-Live

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 15 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation blocked until all specs 01-14 are complete |
| Depends on | Specs `01_foundation-and-access` through `14_observability-and-alerting` (each checklist must be complete before this spec is implemented) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `registry-and-policy-v1.md` (`REG`), `database-v1.md` (`DB`), `access-and-secrets-v1.md` (`SEC`), `app-release-v1.md` (`REL`), `backup-and-recovery-v1.md` (`BKP`), `observability-v1.md` (`OBS`), `central-deployment-v1.md` (`DEP`) |
| Design | `docs/design/variables-and-secrets.md` §§2, 5, 10-11; `docs/design/naming-and-repository-conventions.md` §8; v5 design §§2, 4.1, 7.1-7.2, 9.3, 11.3, 12.3, 13.1-13.3, 15.2, 15.5, 16 steps 2, 10-11, 17 item 6 |

## What

Deliver the operator-facing app onboarding contract, rehearse the required Staging credential rotations, review capacity at the fourth-app trigger, and record evidence for every Production go-live gate. Onboarding must use the existing CentralDevOps workflows and policy; it must not create an app-specific path around them.

## Context

- The roadmap's numeric order still applies. This spec may be implemented only after every checklist for specs 01-14 is complete. Drafting it does not waive specs 13 or 14, authorize a Production deployment, or allow any gate to be skipped.
- Specs 02 and 03 own the throwaway-app trust proof and disposable-host hardening proof. Specs 06, 08-12 own the registry, database, build, authorization, deployment, and request contracts. This spec consumes their completed behavior and evidence rather than reimplementing it.
- The onboarding flow follows v5 §15.2: reviewed CentralDevOps registry PR and capacity check, DNS, app-owned workflow/configuration and Environments, then build, Staging verification, and Production. Adding an app must not require edits to CentralDevOps workflows.
- The app owns its source, Dockerfile, Compose file, manifests, app runtime configuration, and schema migrations. CentralDevOps owns placement, registry policy, deployment credentials, and the Production approval gate.
- Production remains blocked until all five parent PRD §8 gates are recorded as passed in `docs/runbooks/production-go-live-record.md`.
- Capacity is enforced by spec 06 using the reviewed per-host memory budget from spec 03. This spec must not invent a CPU host budget or hard-code VPS sizing. REG-12 is triggered by the fourth distinct app; if that event has not occurred, record it as not yet triggered rather than claiming a review passed.

## Requirements

| ID | Statement | Source |
|---|---|---|
| REG-09 | Onboard an app without changing CentralDevOps workflows: reviewed Staging and Production registry entries pass capacity checks, DNS is configured, the app repository has its workflows/configuration/Environments/runtime secrets/dispatch credentials, and the app is built, deployed to Staging, verified, then deployed to Production. | Registry and Policy PRD REG-09; v5 §15.2 |
| REG-10 | Document the app contract: Dockerfile, `compose.yml`, per-Environment manifest, health endpoint, stateless containers, durable data outside the writable layer, runtime configuration through environment variables, and no secrets in image layers, build arguments, labels, or committed Compose files. | Registry and Policy PRD REG-10 |
| REG-11 | Record the container user for each app and use a non-root user where the app allows it. | Registry and Policy PRD REG-11; v5 §12.3 |
| REG-12 | Review sizing when the fourth app is onboarded and retain a review record. | Registry and Policy PRD REG-12; v5 §§2, 9.3 |
| DB-06 | App teams own schema migrations and keep them backward compatible with the previous release. CentralDevOps runs no migration except an app-declared optional release command. | Database PRD DB-06; v5 §11.3 |
| SEC-16 | Document and rehearse the admin and deploy SSH key, sealed-bundle key, registry pull token, dispatch App key, and backup repository password rotations on Staging without a deployment outage. The age-key transition accepts two recipients. | Access and Secrets PRD SEC-16; v5 §15.5 |
| SEC-18 | Once a deployment team is assigned, use the chosen team/owner model for the CentralDevOps Production Environment required reviewer. | Access and Secrets PRD SEC-18; parent PRD Q6 |
| GL-01 | Record evidence for all five parent PRD Production go-live gates. No Production go-live is authorized until every gate is passed. | Parent PRD §8 |

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Resolve Q6: the owner is the initial CentralDevOps Production required reviewer. Once a deployment team is assigned, that team replaces the owner as the required reviewer; the default is one team approval, not an owner-plus-team double approval. | Keep the owner alongside the team, requiring an additional approval | The team takes operational ownership without adding a second default approval. This matches SEC-18's replacement option and preserves the single CentralDevOps approval path in SEC-15. | Yes |
| D2 | Keep app Production Environments without reviewers by default; the CentralDevOps Production Environment remains the single approval gate. | Add a second app-repository approval | Avoids duplicating the approval required by SEC-05 and SEC-15. | Yes |
| D3 | Treat the fourth-app sizing review as an event-triggered control. If fewer than four distinct apps are registered, publish the procedure and mark the review not yet triggered. | Claim completion using a fixture or block initial Production solely because fewer than four apps exist | REG-12 is a Should requirement tied to the fourth app, not an additional parent PRD go-live gate. | Yes |
| D4 | A gate with missing or inconclusive evidence is `BLOCKED`, not passed. Production cannot proceed until all five gates are `PASS`. | Waive a gate or infer success from another task's completion | The parent PRD requires every gate to be recorded before Production. | No |

## Design

### Application onboarding contract

Create `docs/runbooks/app-onboarding.md` with the following ownership boundaries and ordered flow:

1. The app team proposes `apps/<app>/staging.yml` and `apps/<app>/production.yml` in a reviewed CentralDevOps pull request. Registry validation, domain/port uniqueness, and the spec 06 capacity check must pass. App teams do not edit or copy central workflow logic.
2. Configure the approved DNS records for the registry domains. Do not use unreviewed domains or host placement as app-controlled inputs.
3. In the app repository, provide `build.yml`, `deploy.yml`, `compose.yml`, `deploy/staging.yml`, and `deploy/production.yml`; create exactly the `Staging` and `Production` Environments; configure only the app-owned `APP_*` values/secrets and the selected-repository dispatch App credentials. Never place admin/deploy SSH keys, the registry pull token, or the central age private key in an app repository.
4. Build and publish an immutable image digest, deploy it to Staging, and verify health/routing before requesting Production. The Production request uses the normal central authorization, policy, Environment approval, deployment, and rollback path.
5. Record the app's effective container user. Use non-root where supported; where it is not, record the reason and the app owner's acceptance rather than silently omitting the check.
6. Require a health endpoint and stateless application containers. Persist durable data in an approved volume, database, or object store, not the container writable layer. Supply runtime configuration through environment variables. Never put secrets in image layers, build arguments, labels, committed Compose files, workflow inputs, artifacts, or logs.
7. Preserve the database contract: the app supplies its own `DB_PASSWORD`; platform-owned `DB_HOST`, `DB_PORT`, `DB_NAME`, and `DB_USER` cannot be overridden by the app. App teams own migrations and keep each change backward compatible with the previous release. CentralDevOps does not run schema migrations; an optional release command must be explicitly declared and validated under the existing manifest contract.

The guide must separate CentralDevOps-owned values and review steps from app-owned files and secrets, and include a per-app onboarding checklist that records the container user, any non-root exception, Staging verification, and the evidence/URL for Production approval and result.

### Credential rotation

Create `docs/runbooks/credential-rotation.md`. For each procedure, identify the Staging-only rehearsal steps, safe handoff order, verification, rollback condition, and sanitized evidence to record. The SEC-16 mandatory rehearsal set is:

| Credential | Required safe sequence |
|---|---|
| `ANSIBLE_SSH_PRIVATE_KEY` (admin) | Add and verify the replacement admin public key before removing the old key. Confirm host verification still passes. |
| `DEPLOY_SSH_PRIVATE_KEY` | Add the replacement deploy public key, verify a Staging deployment, then remove the old key. |
| `DEPLOY_RUNTIME_AGE_PRIVATE_KEY` | Publish the new public recipient, make the request path seal for both old and new recipients during overlap, verify a Staging deployment, then remove the old recipient after the transition is confirmed. |
| `GHCR_PULL_TOKEN` | Replace the Staging secret, reconfigure the host, verify a pull of the approved image, then revoke the old token. |
| `DEPLOY_DISPATCH_APP_PRIVATE_KEY` | Replace the selected-repository App secret, verify a Staging dispatch and result correlation, then delete the old App key. |
| `BACKUP_RESTIC_PASSWORD` | Add a new Staging repository key, update the protected recovery copy and host secret, verify backup and restore, then remove the old repository key. |

The design's additional rotation rows for `BACKUP_S3_*`, `MONITORING_GRAFANA_CLOUD_TOKEN`, and app `APP_*` secrets remain documented where those credentials are used. They do not replace any mandatory SEC-16 rehearsal. Never include a secret, key, token, runtime environment value, or sealed bundle in an implementation summary.

### Fourth-app capacity review

Create `docs/runbooks/capacity-review.md` with a reusable review record. Trigger it when the fourth distinct app is onboarded, not when a duplicate Environment registry entry is added. The review must:

- Record the app count, review date, reviewer, and registry/inventory revisions.
- Confirm each used host still has a valid reviewed `capacity_budget_mib` and compare the sum of registered app memory limits against that budget using the spec 06 result.
- Review per-app CPU and memory ceilings and available Staging/Production host observations. Distinguish enforced memory budget from observational signals; do not introduce a host CPU budget or change a budget without a reviewed inventory PR.
- Record headroom, any concern, the decision (`no change`, follow-up, or reviewed sizing change), and the owner/date for follow-up.

If the fourth-app trigger has not occurred, the onboarding guide must retain the trigger and the record must explicitly say `not yet triggered`. A fixture can test the calculation but cannot be represented as the required fourth-app review.

### Production go-live record

Create `docs/runbooks/production-go-live-record.md` and record a status, evidence link/reference, date, and decision owner for each of these exact gates:

| Gate | Required evidence |
|---|---|
| 1 | Throwaway-app acceptance passed (DEP-20). |
| 2 | Host hardening proven safe on a disposable VPS (INF-16). |
| 3 | A Staging deployment passed and rollback was rehearsed (REL-13, DEP-12). |
| 4 | S3 endpoint verified and a timed restore completed within four hours (BKP-08, BKP-10). |
| 5 | Host-down and backup-age alerts are active, and DNS TTL handling for recovery is decided (OBS-05, BKP-13). |

Use only `PASS`, `FAIL`, or `BLOCKED`. `PASS` requires dated, sanitized evidence from the owning spec's accepted task summary or run record. Do not copy secret-bearing logs or credentials into the gate record. Any `FAIL` or `BLOCKED` status means Production is not ready; resolve the failure and update the record before the Production request.

## Invariants

| Invariant | How to check |
|---|---|
| Onboarding a second app does not require a CentralDevOps workflow edit. | Compare the CentralDevOps workflow tree before and after the app onboarding proof; review the registry and app-repository changes. |
| Registry and capacity policy remain centrally reviewed. | Confirm the registry PR passed the existing spec 06 checks and no app manifest controls placement or resource ceilings. |
| App secrets and platform credentials remain in their designated repositories/scopes. | Review secret names/scopes and canary logs; never print secret values. |
| Apps use backward-compatible, app-owned migrations. | Review the onboarding contract, manifest release command, and deployed app migration behavior. |
| Every SEC-16 rotation is rehearsed on Staging without a deployment outage. | Check the dated rotation record for each mandatory credential and successful post-rotation verification. |
| Production has exactly the intended CentralDevOps reviewer model and remains protected by `main`. | Inspect CentralDevOps and app Environment settings; app Production has no reviewer by default. |
| Production go-live is blocked unless gates 1-5 are all `PASS`. | Review the go-live record and confirm the deployment approval path cannot bypass the Production Environment. |

## Error Behavior

| Situation | Behavior |
|---|---|
| Any spec 01-14 checklist is incomplete. | Do not start implementation tasks in this spec. |
| Registry validation, capacity validation, or the app contract fails. | Stop onboarding; fix the reviewed registry or app-owned inputs through their normal review paths. Do not weaken central workflows or policy. |
| A rotation's replacement credential fails verification. | Retain the old credential, stop the rotation, and follow the documented rollback. Do not revoke the last known-good credential. |
| An age-key transition cannot decrypt with both intended recipients. | Stop before removing either recipient; restore the known-good action/recipient pair and retry the Staging rehearsal. |
| The fourth app has not been onboarded. | Record the capacity review as `not yet triggered`; do not claim REG-12 passed based on fixtures. |
| A go-live gate is missing, failed, or inconclusive. | Record `BLOCKED` or `FAIL`; do not approve or dispatch a Production deployment. |
| The required deployment team is not assigned. | Keep the owner as the initial Production reviewer; record the team handoff as pending and do not claim SEC-18's post-assignment configuration is complete. |

## Testing Strategy

- Review `app-onboarding.md` against REG-09/10/11, DB-06, specs 06, 08-12, and the actual workflow/manifest interfaces.
- Use a second disposable app repository to follow the onboarding guide. Verify that registry CI and the capacity check pass, Staging works, and no CentralDevOps workflow changes are needed. Do not attempt Production until the gate record is all `PASS`.
- Rehearse every SEC-16 credential class on Staging with the old credential retained until the replacement passes its verification. Confirm there is no deployment outage and no secret in logs, artifacts, task summaries, or runbook evidence.
- Test the capacity-review worksheet with fixtures, then use real reviewed registry/inventory revisions for the fourth-app review. Clearly distinguish fixture results from a triggered review.
- Verify every Production gate against the evidence produced by its owning spec; missing evidence is a failure of readiness, not a reason to weaken the gate.
- For final acceptance, complete the second-app flow through Production only after all five gates are `PASS` and the normal CentralDevOps Production approval is available. If a gate is not ready, stop and leave the final acceptance task blocked.
- At each task close, write `summaries/task-<n>-summary.md` with changed files, verification commands/results, dates, and sanitized evidence references only.

## Deliverables

```text
docs/runbooks/app-onboarding.md
docs/runbooks/credential-rotation.md
docs/runbooks/capacity-review.md
docs/runbooks/production-go-live-record.md
docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/
  checklist.md
  tasks/task-<n>-<task-name>.md
  summaries/task-<n>-summary.md          # written when each task closes
```

## Out of scope

- Implementing or changing registry validation, Compose policy, capacity enforcement, build, authorization, deployment, rollback, backup, or monitoring behavior owned by specs 01-14.
- Adding a new app-specific CentralDevOps workflow, starter-template product, deployment transport, or exception to the central review path.
- Rotating Production credentials as part of the Staging rehearsal.
- Inventing or hard-coding per-host capacity budgets or a host CPU budget.
- Running app schema migrations from CentralDevOps, making app migrations backward-incompatible, or treating a container restart as a data migration.
- Production deployment before the five parent PRD gates are passed and recorded.
