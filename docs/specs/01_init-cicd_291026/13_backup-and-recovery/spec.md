# Spec 13: Backup and Recovery

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 13 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation blocked until specs 08, 11 and 12 are complete |
| Depends on | `08_shared-database`, `11_deploy-execution-and-rollback` and `12_app-deploy-request` (each checklist must be complete before this spec is implemented) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (`BKP`), `database-v1.md` (`DB`), `routing-and-tls-v1.md` (`RTE-12`), `central-deployment-v1.md` (`DEP-14`), `app-release-v1.md` (`REL-13`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §8; `docs/design/naming-and-repository-conventions.md`; `docs/design/variables-and-secrets.md` §§3.2, 4.6–4.7, 7; v5 design §§13.1–13.4, 16 step 10, 17 items 2–3 |

## What

Deliver per-Environment Restic repositories in Sumopod S3, scheduled PostgreSQL and durable application-data backups, post-deployment record/configuration capture, a guarded database restore playbook, and an exercised disaster-recovery runbook. The implementation must provide a timed Staging recovery drill and a secret-free backup-health signal. Spec 14 owns the dashboard and end-to-end backup-age alert wiring; Production remains blocked until that alert is tested.

## Context

- Sumopod does not provide VPS snapshots. CentralDevOps code and verified off-host backups are the recovery path for a lost host; the targets are RTO 4 hours and RPO 12 hours.
- The roadmap permits implementation only after the checklists for specs 08, 11 and 12 are complete. Drafting this spec does not waive those gates or authorize Production changes.
- Spec 08 owns the PostgreSQL host and per-app database contract. Specs 11 and 12 own deployment records, immutable release digests and the app-side release flow. This spec consumes those outputs and does not duplicate their deployment or database-provisioning logic.
- The v5 design selects Restic, one encrypted repository per Environment, and Sumopod S3. This spec makes the outstanding provider, DNS TTL and retention choices explicit without claiming unverified provider capabilities.
- Only validated persistent application paths are backed up. Container writable layers are never a durable-data source. BKP-16 object-storage migration remains deferred.
- The deployed app's runtime environment file contains secrets. It is not copied into the backup set; the app's normal authorized deploy flow reconstructs runtime configuration from its matching GitHub Environment during recovery.

## Requirements

| ID | Statement | Source |
|---|---|---|
| BKP-01 | Export every PostgreSQL database and global objects at intervals of 6 hours or less, then store the verified exports off-host. | Backup and Recovery PRD; v5 §13.2 |
| BKP-02 | Back up persistent app data at least daily unless that app uses object storage. After each authorized host deployment attempt, capture its deployment record and non-secret deployed configuration. | Backup and Recovery PRD; DEP-14; v5 §§13.2, 13.4 |
| BKP-03 | Use one Restic repository per Environment with client-side encryption and a unique, high-entropy password for each Environment. | Backup and Recovery PRD; v5 §13.2 |
| BKP-04 | Keep each human recovery copy of the repository password in the organization password manager, accessible to at least two authorized operators and separate from S3 credentials and the VPS, repository and bucket. | Backup and Recovery PRD; v5 §13.2 |
| BKP-05 | Use least-privilege S3 credentials. Enable provider-side encryption and versioning when supported, and record the verified status of each feature. | Backup and Recovery PRD; parent PRD Q2 |
| BKP-06 | Retain a 14-day rolling backup window plus the monthly recovery points selected by this spec; make the retention policy explicit per Environment. | Backup and Recovery PRD; parent PRD Q4 |
| BKP-07 | Make each backup run's result observable and raise the backup-age alert when the newest good backup is older than 8 hours. | Backup and Recovery PRD; OBS-02, OBS-03, OBS-05 |
| BKP-08 | Before Production, verify the Sumopod S3 endpoint with a test backup and an isolated Staging restore. | Backup and Recovery PRD |
| BKP-09 | Provide and exercise `playbooks/restore-database.yml` and a written disaster-recovery runbook. | Backup and Recovery PRD; v5 §13.3 |
| BKP-10 | Run and record a timed Staging restore before Production go-live and at least quarterly afterwards; the measured recovery must be 4 hours or less. | Backup and Recovery PRD; parent PRD NFR-01, NFR-03 |
| BKP-11 | Document and exercise the lost-VPS sequence: create a replacement VPS manually, update DNS or reassign the IP, bootstrap/configure, restore PostgreSQL and durable app data, redeploy each app at its last known digest, then verify and smoke-test. | Backup and Recovery PRD; v5 §13.3 |
| BKP-12 | Recover each app's last known-good digest without the lost VPS, using app run history and off-host deployment records; never substitute a mutable tag. | Backup and Recovery PRD; REL-13; DEP-14 |
| BKP-13 | Choose and document DNS TTL handling that keeps recovery within the RTO. | Backup and Recovery PRD; parent PRD Q3 |
| BKP-14 | Keep durable app files out of container writable layers and include only explicitly approved persistent paths in file backups. | Backup and Recovery PRD; REG-05, REG-08 |
| BKP-15 | Document certificate-authority rate limits and a safe fallback for reissuing certificates after a rebuild. | Backup and Recovery PRD |
| RTE-12 | State how many Production domains can be reissued in a recovery wave and what operators do if the certificate authority rate-limits issuance. | Routing and TLS PRD; v5 §13.3 |

## Design

### Backup sources and cadence

| Data class | Capture contract | Recovery use |
|---|---|---|
| PostgreSQL | At least every 6 hours, export each non-template database in a `pg_restore`-compatible format and export global objects with `pg_dumpall --globals-only`. Capture and verify the complete set as one successful backup run. | Restore globals and databases to the replacement host before deploying apps. |
| Persistent application data | At least daily, back up only the persistent volume or host paths approved by the registry and Compose policy. Do not read container writable layers. | Restore files to the replacement host before starting the affected app. |
| Deployment records and deployed configuration | After each authorized host deployment attempt is finalized, capture its secret-free record and non-secret deployed configuration. A failed or interrupted deployment must not be recorded as successful. | Identify the last known-good digest and reconstruct the deployed release. |

Restic snapshots go to the matching Environment's repository. PostgreSQL dump files are temporary, root-only working data; remove them after the snapshot attempt and never print, upload as CI artifacts, or retain them as plaintext backups. A snapshot is good only after every required input for that backup class has been captured and Restic has confirmed the repository write.

Database and file snapshots are separate capture events, not a transactionally consistent snapshot across an app and PostgreSQL. Record each class's timestamp and snapshot identifier; the runbook must select compatible restore points and call out any application consistency limitation.

### Repository, secrets and provider controls

- Preserve the v5 layout: one Sumopod S3 bucket with one Restic repository per Environment. Derive stable repository prefixes from the Environment (`staging` and `production`) in reviewed role code; do not add a caller-controlled repository path or `BACKUP_S3_PREFIX` variable in v1.
- Read endpoint, region and bucket from the existing Environment variables `BACKUP_S3_ENDPOINT`, `BACKUP_S3_REGION` and `BACKUP_S3_BUCKET`. Use separate S3 access keys and Restic passwords for Staging and Production. Scope access to the matching repository prefix where Sumopod supports it; otherwise record the narrowest available scope and the residual cross-prefix risk. Never use account-wide administrative credentials.
- Keep Restic client-side encryption mandatory regardless of S3 server-side encryption support. Generate a unique, high-entropy `BACKUP_RESTIC_PASSWORD` of at least 32 characters per Environment. The human recovery copy belongs in the organization password manager with access for at least two authorized operators, in a separate entry from S3 credentials and outside the VPS, repository and bucket.
- The backup host needs root-only operational copies of its matching Environment's S3 credentials and Restic password to write encrypted snapshots. This is distinct from the off-host human recovery copy. Treat BKP-04's separation rule as applying to recovery custody; confirm this interpretation with the PRD owner before implementation because a literal ban on operational co-residence conflicts with the v5 automation design.
- Verify Sumopod's provider-side encryption, versioning and access-scope capabilities using current provider evidence. Enable supported protections and record unsupported features as unavailable. Do not infer support or use provider-side protection as a substitute for Restic encryption.

### Retention and health contract

- Retain all Restic snapshots in the most recent 14-day window and one monthly recovery point for each of the most recent 12 months. Keep deployment records recoverable off-host for at least 12 months.
- Keep `BACKUP_RETENTION_DAYS` at its existing default of `14` and add `BACKUP_RETENTION_MONTHS` with a default of `12`; both are Environment-scoped variables. The value is not permitted to reduce the required 12-month deployment-record retention without an approved spec change.
- Run retention pruning only against the selected Environment's repository, after a successful backup and repository verification. Serialize backup, check and prune operations; a failed check must not trigger pruning.
- Write an atomic, root-owned, secret-free backup status document at `/var/lib/centraldevops/backups/status.json`. It records the last attempt and last successful completion per backup class, sanitized result/error code, and verified snapshot identifier. Preserve the last-success time when a later attempt fails.
- Extend `verify-vps.yml` to report failure when the newest good backup is older than 8 hours. Expose the status document through a read-only monitoring path for spec 14, which owns the dashboard and end-to-end alert delivery test.

### Restore and disaster recovery

- `playbooks/restore-database.yml` restores global objects and per-database exports from the selected Environment's Restic repository. A restore drill must use an explicitly isolated target; the playbook must not silently overwrite the live Staging or Production database.
- The runbook follows the BKP-11 sequence and includes time budgets for every step, including durable app data, app redeploys and verification. It uses the app's run history plus off-host deployment records to select a full image digest, then invokes the normal authorized deployment path.
- Set Production A/AAAA TTLs to 300 seconds before Production go-live and keep that value for v1. Confirm the authoritative and publicly observable TTLs before declaring the DNS recovery budget valid; do not assume Sumopod can reassign an IP.
- For certificate recovery, use the CA staging endpoint in drills. Before Production, count active Production domains from the registry, check the current official Let's Encrypt limits, and record a numeric safe issuance-wave size and retry window in the runbook. If rate-limited, stop repeated issuance attempts, leave affected domains unavailable rather than serving plain HTTP or an invalid certificate, continue unaffected recovery work, and retry after the documented window.
- A timed Staging drill uses an isolated replacement target and the Staging credentials only. Record elapsed time, the restored snapshot, restored data classes, digest sources, verification results and any excluded production-only DNS/CA steps. Do not claim the RTO passed if required steps were skipped or the measured total exceeds 4 hours.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Keep one S3 bucket and derive separate `staging` and `production` repository prefixes from the selected Environment. | Separate buckets or operator-supplied prefixes | Preserves the v5 topology and avoids a mutable path input that could cross Environment boundaries. Provider access-scope limitations must be recorded. | Yes |
| D2 | For Q2, verify provider-side encryption, versioning and prefix-scoping; enable each supported feature, record unsupported features, and always retain Restic client-side encryption. | Assume support or treat provider encryption as sufficient | The design requires provider features only when available; the evidence must reflect the actual Sumopod account. | Yes |
| D3 | For Q3, lower and maintain Production DNS A/AAAA TTL at 300 seconds before go-live. | Keep the current 14,400-second TTL or rely on retaining the same IP | A short, pre-established TTL supports the 4-hour RTO without relying on unconfirmed IP reassignment. If the DNS provider cannot honor it, block go-live pending a reviewed alternative. | Yes |
| D4 | For Q4, retain 12 monthly Restic recovery points and keep off-host deployment records for at least 12 months, in addition to the 14-day window. | Retain an unspecified "few" monthly copies or keep only the current deployment record | A one-year policy gives an explicit recovery and audit horizon; Restic deduplication limits repeated data storage. | Yes |
| D5 | Back up only secret-free deployed configuration and deployment records; exclude decrypted runtime files, credentials, private keys and sealed request bundles. | Treat the backup repository as another secrets vault | Runtime configuration is regenerated through the matching app Environment and authorized deploy flow; excluding secrets limits backup access impact. | Yes |
| D6 | Assumption: interpret BKP-04's separation requirement as applying to the human recovery copy, not the root-only operational copies needed on the backup host. | Prohibit the backup host from holding both runtime inputs | Restic requires the host to access both its S3 destination and repository password. The assumption must be accepted before implementation; otherwise the PRD/design conflict must be resolved first. | No, pending review |

## Invariants

| Invariant | How to check |
|---|---|
| Staging and Production use different repository prefixes, S3 credentials and Restic passwords. | Inspect sanitized role configuration and prove a repository cannot be opened with the other Environment's password. |
| Restic client-side encryption is always enabled. | Restore with the correct password and verify that an incorrect password cannot open the repository. |
| A backup is marked good only after all required sources for that class are captured and the Restic snapshot is verified. | Inject a missing database, failed dump and failed S3 write; confirm none advances the last-success timestamp. |
| No runtime `.env`, credential, private key or decrypted bundle enters a snapshot, log, status file, artifact or task summary. | Use synthetic canary values and scan generated outputs and restored test snapshots. |
| Durable application data is sourced only from approved persistent mounts, never a container writable layer. | Compare backup sources with registry/Compose policy and restore a test volume's marker file. |
| A database restore drill cannot target a live Production or Staging database implicitly. | Exercise missing, mismatched and isolated target inputs; all unsafe cases fail before mutation. |
| The recovery digest is immutable and corroborated by app run history and an off-host deployment record. | Simulate loss of the host and verify the selected digest without consulting host-local files. |
| Production go-live remains blocked until the timed restore, S3 verification, DNS decision and backup-age alert evidence are complete. | Review the spec 15 go-live gate record and spec 14 alert test. |

## Error Behavior

| Situation | Behavior |
|---|---|
| A database export is missing, incomplete or fails. | Fail that backup run, preserve the previous last-success timestamp, clean up temporary plaintext, and emit a sanitized failure status. |
| S3 authentication, upload or Restic verification fails. | Do not mark the snapshot good, do not silently switch Environment/repository, and expose the failure for monitoring. |
| Retention configuration is invalid, repository verification fails, or backup and prune overlap. | Do not prune; report the failure and keep existing snapshots unchanged. |
| A restore password is unavailable or a repository cannot be opened. | Stop before database or application mutation and direct operators to the documented recovery-custody path. Never print the password. |
| A restore target is absent, live, or belongs to the wrong Environment. | Fail closed before restore; do not fall back to an implicit target. |
| Required app runtime secrets are unavailable during recovery. | Do not start a partially configured app or restore plaintext secrets from the backup; pause that app's recovery and report the missing prerequisite without values. |
| The CA rate-limits certificate issuance. | Stop retries for affected domains, keep valid existing certificates where available, do not serve plain HTTP, and resume only after the runbook's documented retry window. |
| The last good backup is older than 8 hours or missing. | Report `FAIL` in verification and expose a stale/missing signal for the spec 14 alert; never convert a failed run into a successful backup. |

## Testing Strategy

- Verify each Environment's S3 endpoint with a test snapshot, Restic repository check, correct-password restore and wrong-password rejection. Record provider-side encryption, versioning and access-scope capability evidence.
- Test the six-hour PostgreSQL schedule with multiple databases and global roles; restore all exports into a clean isolated PostgreSQL target and compare database/role inventories.
- Test daily app-data backups from approved persistent mounts, post-deployment capture of both successful and failed deployment records, and exclusion of runtime secrets and container writable layers.
- Exercise the 14-day and 12-month retention policy in a disposable repository. Prove a failed or unchecked repository cannot be pruned and an Environment's prune cannot affect the other prefix.
- Inject backup, verification and status-write failures; confirm the last-success timestamp is preserved and `verify-vps.yml` reports a backup older than 8 hours as `FAIL`.
- Run the database restore playbook against an isolated Staging target; prove no live database is mutated and restored global objects and databases are usable.
- Execute the runbook on a disposable Staging replacement target before Production go-live and quarterly thereafter. Include the S3 restore, durable app data, digest-based redeploy, verification and smoke test; the measured elapsed time must be at most 4 hours.
- Use only synthetic data and the CA staging endpoint in tests. No Production S3 credential, Production database, Production certificate request or secret value may appear in test output.
- Record sanitized date, commands, run URLs/IDs, outcomes and elapsed times in each task summary after acceptance.

## Deliverables

```text
roles/backup/                                  # Restic setup, schedules, capture, retention and status
playbooks/restore-database.yml                 # guarded restore of PostgreSQL exports
playbooks/configure.yml                         # include backup role in the approved configure profile
playbooks/verify.yml                            # expose backup freshness through verify-vps.yml
docs/runbooks/backup-and-disaster-recovery.md  # recovery sequence, budgets, DNS and certificate limits
docs/design/variables-and-secrets.md            # record BACKUP_RETENTION_MONTHS and custody decisions
deployment/tools/tests/                         # focused backup, retention and restore checks
```

Task summaries belong in `summaries/task-<n>-summary.md` and are written only when their implementation task closes. The backup-age alert delivery is completed by spec 14; this spec supplies its status contract and handoff.

## Out of scope

- BKP-16 upload migration to object storage; app-owned uploads remain backed up from approved persistent volumes.
- Automated VPS provisioning, Sumopod APIs, automated DNS changes, continuous database replication, point-in-time recovery or whole-VPS snapshots.
- Storing decrypted runtime files, age bundles, S3 credentials, Restic passwords or other private keys in the backup repository.
- Grafana dashboards and end-to-end alert notification setup (spec 14), although the backup-age signal and go-live dependency are defined here.
- Production restore drills or Production CA issuance as a test.
