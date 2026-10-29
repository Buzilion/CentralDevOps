# Task 3: Database, certificate, and backup signals

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Task 1 |
| Needs | Completed spec 07/08/13 role contracts and Staging host |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Integrate PostgreSQL availability/connections and the existing certificate and backup health sources without duplicating their owners' state.

## Relevant files or references

- `roles/postgresql/`
- `roles/monitoring_agent/`
- `roles/backup/`
- `/var/lib/centraldevops/metrics/certificate-expiry.prom` (spec 07)
- `/var/lib/centraldevops/backups/status.json` (spec 13)
- Spec 07 `centraldevops_certificate_expiry_days` contract
- Spec 13 Task 4 and Task 8 backup status/observability handoff
- OBS-02, OBS-03, OBS-05; DB-01 to DB-03; BKP-07

## Proposed approach

1. Add PostgreSQL exporter access through a dedicated local read-only monitoring identity with only the statistics-monitoring capability. Keep its endpoint local/private and do not collect query text or parameters.
2. Scrape spec 07's certificate-expiry metric read-only. Preserve the under-21-days threshold and treat a certificate as not applicable only when the registry expects no route.
3. Read spec 13's root-owned `/var/lib/centraldevops/backups/status.json` through its read-only monitoring interface. Do not change the document, obtain S3/Restic credentials, or add another backup-status file.
4. Derive `centraldevops_backup_last_success_timestamp_seconds` from the newest verified success using the same definition as spec 13's verifier. Preserve the 8-hour threshold and do not advance the metric after a failed backup.
5. Test missing, stale, malformed, and fresh PostgreSQL/certificate/backup signals, including threshold-boundary values.

## Acceptance criteria

- PostgreSQL availability and connection metrics are queryable without public exporter access or mutation privileges.
- Certificate metrics are consumed from spec 07's existing source; no duplicate certificate state is introduced.
- Backup age is derived read-only from spec 13's status document and matches spec 13's "newest good backup" calculation.
- The backup-age alert source is stale when the latest verified success is older than 8 hours and does not become fresh after a failed attempt.
- No S3 credential, Restic password, database secret, SQL parameter, or snapshot content is exposed to the collector.

## Source reference

OBS-02, OBS-03, OBS-05; DB-02; BKP-07; v5 §§11.1, 13.1–13.2; spec 07 certificate metric contract; spec 13 Tasks 4 and 8.

## Verify

- Query PostgreSQL metrics through the dedicated identity; verify the identity cannot change database state.
- Test certificate samples below, at, and above 21 days and preserve spec 07's no-route behavior.
- Test backup-status fixtures for missing, fresh, stale, malformed, and failed-last-attempt cases; compare the derived result with spec 13's verifier.
- Inspect the read-only permission boundary for `status.json` without displaying credential-bearing backup files.

## Out of scope

PostgreSQL provisioning, certificate issuance/renewal, backup scheduling/retention, and end-to-end notification delivery.
