# Checklist for 01_init-cicd_291026/13_backup-and-recovery

Implementation is blocked until every task in `08_shared-database/checklist.md`, `11_deploy-execution-and-rollback/checklist.md` and `12_app-deploy-request/checklist.md` is checked off. Continue in roadmap numeric order; drafting this spec does not waive those gates. Confirm the BKP-04 recovery-copy interpretation before implementation. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is accepted.

- [ ] Task 1: s3-repository-and-key-custody - verify provider capabilities, initialize isolated Restic repositories and establish recovery-key custody
- [ ] Task 2: postgresql-export-schedule - export all databases and global objects at least every 6 hours
- [ ] Task 3: persistent-data-and-deployment-backups - capture approved app data daily and deployment records/configuration after each attempt
- [ ] Task 4: retention-and-backup-health-contract - enforce retention, expose backup status and extend host verification
- [ ] Task 5: restore-database-playbook - add a guarded restore playbook and prove isolated database recovery
- [ ] Task 6: recovery-runbook-and-certificate-limits - document RTO budgets, DNS TTL, digest recovery and CA-rate-limit fallback
- [ ] Task 7: timed-staging-restore-drill - execute the runbook from S3 on an isolated Staging replacement target within 4 hours
- [ ] Task 8: backup-readiness-and-observability-handoff - verify BKP/RTE traceability and hand off the alert signal to spec 14
