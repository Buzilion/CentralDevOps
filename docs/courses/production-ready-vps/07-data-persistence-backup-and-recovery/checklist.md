# Data Persistence, Backup, and Recovery — Course Checklist

Complete this subject after **Linux Server Administration**, **Networking, DNS, and Firewall Security**, **Docker and Container Operations**, **Infrastructure Automation with Ansible**, **CI/CD with GitHub Actions**, and **Reverse Proxy, HTTPS, and Application Serving**. Base every storage and backup decision on the inspected application release and its actual data paths; do not assume it uses PostgreSQL, a local volume, or even stores durable user data on the VPS.

This subject proves that important state can be recovered independently of the live VPS. A named volume, a successful backup command, or a file in a remote bucket is not by itself proof of recovery. Use a disposable or isolated target for experiments. Never overwrite production data during a restore drill. Sanitize evidence and never record database contents, credentials, encryption keys, private infrastructure details, or personal data.

## Lessons

- [ ] [01 — Data inventory, ownership, and recovery objectives](lessons/01-data-inventory-ownership-and-recovery-objectives.md)
- [ ] [02 — Persistence boundaries and consistency](lessons/02-persistence-boundaries-and-consistency.md)
- [ ] [03 — Selecting a backup method for each data class](lessons/03-selecting-a-backup-method-for-each-data-class.md)
- [ ] [04 — Off-site backup architecture, encryption, and access](lessons/04-off-site-backup-architecture-encryption-and-access.md)
- [ ] [05 — Scheduling, retention, and backup verification](lessons/05-scheduling-retention-and-backup-verification.md)
- [ ] [06 — Restore testing and recovery validation](lessons/06-restore-testing-and-recovery-validation.md)
- [ ] [07 — Schema migrations, releases, and recoverable change](lessons/07-schema-migrations-releases-and-recoverable-change.md)
- [ ] [08 — Recovery workflow, incident decisions, and operational evidence](lessons/08-recovery-workflow-incident-decisions-and-operational-evidence.md)

## Hands-on tasks

- [ ] [Task 01 — Inventory state and define measurable recovery objectives](tasks/01-inventory-state-and-define-recovery-objectives.md)
- [ ] [Task 02 — Produce and validate a consistent application backup](tasks/02-produce-and-validate-a-consistent-application-backup.md)
- [ ] [Task 03 — Protect and retrieve an encrypted off-site copy](tasks/03-protect-and-retrieve-an-encrypted-off-site-copy.md)
- [ ] [Task 04 — Automate backup scheduling, retention, and failure visibility](tasks/04-automate-backup-scheduling-retention-and-failure-visibility.md)
- [ ] [Task 05 — Restore into an isolated environment and measure recovery](tasks/05-restore-into-an-isolated-environment-and-measure-recovery.md)
- [ ] [Task 06 — Rehearse a risky release and data-recovery decision](tasks/06-rehearse-a-risky-release-and-data-recovery-decision.md)
- [ ] [Task 07 — Publish and exercise the application recovery runbook](tasks/07-publish-and-exercise-the-application-recovery-runbook.md)

## Subject completion gate

- [ ] Every important data class, stateful path, owner, source of truth, and recovery dependency is identified; unknowns and intentionally ephemeral state are explicit.
- [ ] RPO and RTO are agreed in measurable units and have a design that can meet them; actual recovery evidence is compared with those objectives.
- [ ] Each durable data class has a consistency-appropriate backup method. A live database directory is not copied blindly, and a Docker volume is not treated as an independent backup.
- [ ] At least one usable copy is stored outside the VPS failure and credential boundary, protected with encryption and appropriately restricted access.
- [ ] Backup scheduling, retention, capacity, failure visibility, and restore prerequisites are documented and verified.
- [ ] An encrypted off-site copy has been retrieved, decrypted with a controlled key-recovery process, and restored into an isolated target.
- [ ] Application behavior and representative records/files are validated after restore without exposing or retaining unnecessary real data.
- [ ] Schema/data migrations, release compatibility, and the limits of rollback are understood; recovery decisions account for writes made after a backup.
- [ ] A dated, sanitized recovery runbook identifies decision owners, prerequisites, commands or procedures, validation, measured RPO/RTO, and safe return to service.
- [ ] Restore exercises never overwrote production, exposed a database publicly, or placed backup credentials, secrets, keys, or personal data in course evidence.

## Exit criteria

The VPS is not considered recoverable just because backups run. An operator must be able to obtain a protected backup independently of the server, restore it to a clean isolated environment, validate the application state, and explain the measured recovery time and data-loss window. Finish and review this subject before proceeding to **Monitoring, Logging, and Alerting**.
