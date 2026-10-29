# Checklist for 01_init-cicd_291026/08_shared-database

Implementation is blocked until every task in `04_docker-and-deploy-runtime/checklist.md`, `05_host-verification/checklist.md`, and `06_registry-and-compose-policy/checklist.md` is checked off. Complete the tasks below in order unless a task dependency explicitly permits otherwise. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is done.

- [ ] Task 1: postgresql-host-role - Versioned PostgreSQL role, loopback and `db` gateway listener, SCRAM authentication, and subnet-only firewall rule
- [ ] Task 2: reboot-ordering-and-verification - Docker/network systemd ordering and read-only PostgreSQL checks in `verify-vps.yml`
- [ ] Task 3: per-app-database-provisioning - Registry-derived database and login-role lifecycle, secure password rotation, and rollback interface
- [ ] Task 4: app-connection-contract - Centrally supplied `DB_*` values, app-owned `DB_PASSWORD`, and deployment integration contract
- [ ] Task 5: admin-access-and-migration-path - SSH-tunnel runbook, app-owned database-container path, and separate database-host path
- [ ] Task 6: shared-database-acceptance - Disposable-host isolation, external exposure, reboot, connection, rotation, and rollback proof
