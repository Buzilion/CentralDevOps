# Module PRD: Backup and Disaster Recovery (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `BKP` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

Meeting the recovery targets, **RTO 4 hours and RPO 12 hours**, for each Environment's VPS. Sumopod offers no VPS snapshots, so the only recovery path is the code in CentralDevOps plus the off-host backups.

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| BKP-01 | PostgreSQL is exported every 6 hours (each database plus the global objects) and stored off-host. | Backups complete at intervals of 6 hours or less. The newest backup contains every database on the instance. | §13.2 |
| BKP-02 | Persistent app data (volumes, uploads) is backed up at least daily, unless the app keeps it in object storage. Deployment records and configuration are backed up after each deployment. | A restore of a test app's volume returns its data. The latest deployment record is in the backup after a deployment. | §13.2 |
| BKP-03 | All backups go to one encrypted repository per Environment in the Sumopod S3 bucket, using Restic. The repository password is unique, randomly generated and high-entropy for each Environment. | Backup content cannot be read without the password. Staging and Production passwords differ. | §13.2, §17 #3 |
| BKP-04 | The recovery copy of each repository password is held in the organisation's password manager, accessible to at least two authorised operators. It is stored separately from the S3 credentials and outside the VPS, the repository and the bucket. | Two operators demonstrate access. No single location holds both the S3 credentials and the password. | §13.2 |
| BKP-05 | S3 credentials are least-privilege. Provider-side encryption and versioning are enabled if Sumopod supports them, in addition to the client-side encryption. | The credentials cannot manage anything else on the provider. The status of each provider feature is recorded. | §13.2 |
| BKP-06 | Retention defaults to 14 days (configurable per Environment) plus a few monthly copies. | Snapshots older than the policy are pruned. Monthly copies exist. | §4.3, §13.2 |
| BKP-07 | Backups are monitored: each run's result is observable, and an alert fires when the newest good backup is older than 8 hours (see `observability-v1.md`). | A deliberately failing backup raises the alert within the threshold. | §2, §13.1 |
| BKP-08 | Before Production, the Sumopod S3 endpoint is verified with a test backup and an isolated restore on Staging. | A recorded test backup and isolated restore. | §13.2, §17 #3 |
| BKP-09 | A restore playbook for the database and a written recovery runbook exist and are exercised. | The playbook and runbook exist. The Staging drill is executed from the runbook. | §13.3 |
| BKP-10 | A timed restore drill runs on Staging before Production go-live and at least quarterly afterwards. The elapsed time is recorded against the 4-hour target. The first drill is an isolated restore from the S3 repository. **Production is not ready until a timed restore passes.** | A recorded drill with elapsed time of 4 hours or less before go-live, and one per quarter. | §13.3, §16 step 10 |
| BKP-11 | A lost environment VPS can be rebuilt from code and backups in this order: create new VPS (manual), update DNS or reassign the IP, bootstrap and configure as all-in-one, restore PostgreSQL, redeploy every app at its last known digest, verify and smoke-test. The runbook states a time budget for each step. | The drill follows this sequence using only the runbook, the code and the backups. | §13.3 |
| BKP-12 | The last known-good digest of every app can be found without the lost VPS, from the app run history and the off-host deployment records. | During the drill, every app is redeployed at the digest taken only from those sources. | §13.3, §13.4 |
| BKP-13 | The disaster recovery plan states how the DNS TTL is handled so that it does not exceed the RTO: either lower the TTL on production A/AAAA records beforehand (for example 300–600 s) or keep the same IP on recovery. | The plan records the chosen option. | §13.3 |
| BKP-14 | Durable files are never kept in a container's writable layer. | The registry/Compose policy review confirms every durable path is a volume, the database or object storage. | §13.2 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| BKP-15 | The recovery runbook documents certificate-authority rate limits for reissuing many certificates after a rebuild (see RTE-12). | Runbook section exists. | §13.3 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| BKP-16 | Uploads are moved to object storage so that recovery of app data no longer depends on volume restores. | The app serves uploads from object storage after a rebuild without a volume restore. | §13.2, §14.2 |
