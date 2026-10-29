# Spec Roadmap: 01_init-cicd_291026

Work through the spec folders in numeric order. A spec may start only when every spec in its **Depends on** column is fully checked off in its `checklist.md`. Inside a spec, do the tasks in order unless a task's own `Depends on` line says otherwise.

| Source | Path |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/*-v1.md` (`SEC`, `INF`, `REL`, `DEP`, `REG`, `RTE`, `DB`, `BKP`, `OBS`) |
| Design | `docs/design/*.md` (contracts, naming, variables and secrets); full design at `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§16 is the implementation order this roadmap follows) |

## Folder layout

```text
docs/specs/01_init-cicd_291026/
├── 00_spec-roadmap.md                  # this file
└── NN_<spec-name>/
    ├── spec.md
    ├── checklist.md
    ├── tasks/task-<n>-<task-name>.md   # n restarts at 1 in every spec, 9 tasks at most
    └── summaries/task-<n>-summary.md   # written when a task closes
```

## Order and dependencies

| # | Spec folder | Delivers | PRD requirements owned | Depends on | Go-live gate |
|---|---|---|---|---|---|
| 01 | `01_foundation-and-access` | GitHub Environments, code-owner review, workflow lint, name checker, README plan note | SEC-01, 02, 03 (lint part), 04, 05, 07, 13, 14, 17; SEC-06 (history scan) | none | |
| 02 | `02_dispatch-trust-proof` | Throwaway-app proof of dispatch, OIDC claims and Environment selection; dispatch GitHub App | DEP-20, SEC-10, SEC-15 | 01 | 1 |
| 03 | `03_host-bootstrap-and-hardening` | Inventory, host-key pins, bootstrap workflow, SSH hardening proven on a disposable VPS | INF-01, 02, 07, 08, 09, 10, 13, 14, 15, 16, 19, 20; SEC-03 (password lifecycle) | 01 | 2 |
| 04 | `04_docker-and-deploy-runtime` | Configure workflow and profiles, Docker, `edge`/`db` networks, restricted deploy runtime | INF-03, 04, 05, 11, 12; SEC-06 (deploy key), SEC-11 | 03 | |
| 05 | `05_host-verification` | `verify-vps.yml`, per-role checks, VPS runbooks | INF-06, 17, 18 | 04 | |
| 06 | `06_registry-and-compose-policy` | Registry and manifest schemas, Compose policy, capacity and duplicate checks | REG-01 to 08; RTE-02 (schema) | 01, 03 | |
| 07 | `07_routing-and-tls` | Nginx and Certbot roles, route script, DNS precondition, HTTP-01 and HTTPS | RTE-01 to 06, 08 to 10 | 04, 05, 06 | |
| 08 | `08_shared-database` | PostgreSQL role, per-app database and role provisioning, reboot ordering | DB-01 to 05, 07, 08 | 04, 05, 06 | |
| 09 | `09_app-build-and-provenance` | App `build.yml` pattern: digest, tag, attestation | REL-02, 03, 04, 15 | 01 | |
| 10 | `10_deploy-authorization` | `deploy-app.yml` authorize and preflight stages, OIDC verifier, replay protection | DEP-01 to 07, 10 (validation), 13, 16 | 02, 06, 09 | |
| 11 | `11_deploy-execution-and-rollback` | Deploy stage, health check, rollback, locks, records, smoke test, approval wait | DEP-08, 09, 11, 12, 14, 15, 17, 18, 19; RTE-07, 11; SEC-12 | 04, 07, 08, 10 | 3 (rollback) |
| 12 | `12_app-deploy-request` | `request-deploy` action and app `deploy.yml`, sealing, rollback by digest | REL-01, 05 to 14; SEC-08, 09 | 10, 11 | 3 |
| 13 | `13_backup-and-recovery` | Restic to S3, schedules, restore playbook, DR runbook, timed drill | BKP-01 to 15; RTE-12 | 08, 11, 12 | 4 |
| 14 | `14_observability-and-alerting` | Collector, dashboards, alerts, external probe, quota tracking | OBS-01 to 08 | 05, 13 | 5 |
| 15 | `15_onboarding-and-go-live` | Onboarding guide and contract, rotation rehearsals, capacity review, go-live gate record | REG-09 to 12; DB-06; SEC-16, 18; all gates | 01 to 14 | 1 to 5 |

Go-live gates are the five listed in the parent PRD §8: (1) throwaway-app test, (2) hardening proven safe, (3) Staging deploy with rehearsed rollback, (4) S3 verified and timed restore passes, (5) host-down and backup-age alerts active and DNS TTL decided.

## Decisions that shape the order

- **Registry schema moved from §16 step 1 to spec 06.** The registry has no consumer before the Compose policy and capacity check, so it is built with them. Spec 02 uses an inline fixture for its repository-to-app mapping.
- **`ansible.cfg`, `requirements.yml` and inventories move to spec 03**, where the Ansible version is first used and pinned.
- **`verify-vps.yml` is delayed to spec 05**, after the first roles exist, and every later role spec adds its own checks to it (INF-18).
- **Could requirements are not delivered:** INF-21, INF-22, SEC-19, REL-16, RTE-13, RTE-14, REG-13, DB-09, BKP-16, OBS-09, DEP-21. Their contracts stay documented in the PRDs.
- **Open PRD questions are decided in the spec that first needs them:** Q9 and Q7 (host budget values) in spec 03; Q8 in 07; Q11 in 12; Q2, Q3 and Q4 in 13; Q5 and Q10 in 14; Q6 in 15. Q1 only affects Could requirements. Q12 (refreshing the v3 companion documents) is superseded by these specs and `docs/design/`. Each spec lists the ones it owns.

## Status

| # | Spec | Status |
|---|---|---|
| 01 | `01_foundation-and-access` | Spec and tasks written, awaiting review |
| 02 | `02_dispatch-trust-proof` | Spec and tasks written; implementation gated on completion of 01 |
| 03 | `03_host-bootstrap-and-hardening` | Spec and tasks written, awaiting review; implementation is gated by spec 01 |
| 04 | `04_docker-and-deploy-runtime` | Spec, checklist and tasks written; implementation gated on completion of 03 |
| 05 | `05_host-verification` | Spec, checklist and tasks written; implementation gated on completion of 04 |
| 06 | `06_registry-and-compose-policy` | Spec, checklist and tasks written; implementation gated on completion of 01 and 03 |
| 07 | `07_routing-and-tls` | Spec, checklist and tasks written; implementation gated on completion of 04, 05 and 06 |
| 08 | `08_shared-database` | Spec, checklist and tasks written, awaiting review; implementation gated on completion of 04, 05 and 06 |
| 09 | `09_app-build-and-provenance` | Spec, checklist and tasks written, awaiting review; implementation gated on completion of 01 |
| 10 | `10_deploy-authorization` | Spec, checklist and tasks written, awaiting review; implementation gated on completion of 02, 06 and 09 |
| 11 | `11_deploy-execution-and-rollback` | Spec and tasks written, awaiting review; implementation gated on completion of 04, 07, 08 and 10 |
| 12 | `12_app-deploy-request` | Spec, checklist and task breakdown drafted, awaiting review; implementation gated on completion of 10 and 11 |
| 13 | `13_backup-and-recovery` | Spec, checklist and tasks written, awaiting review; implementation gated on completion of 08, 11 and 12 |
| 14 | `14_observability-and-alerting` | Spec, checklist and 8 tasks written, awaiting review; implementation gated on completion of 05 and 13; delivery acceptance also requires approved alert routing and plan fit |
| 15 | `15_onboarding-and-go-live` | Spec and tasks written, awaiting review; implementation gated on completion of 01 to 14 |

Specs 12 and 14 are drafted ahead of numeric order. Specs 10 to 13 are drafted; implementation remains blocked until each spec's dependency checklists are complete. Spec 14 also requires owner approval of alert routing and demonstrated plan fit before delivery acceptance. These drafts do not authorize implementation before all roadmap gates are complete.
