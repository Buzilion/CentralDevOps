# Checklist for 01_init-cicd_291026/14_observability-and-alerting

Implementation is blocked until every item in `05_host-verification/checklist.md` and `13_backup-and-recovery/checklist.md` is complete. Continue in roadmap order; drafting this spec does not waive spec 13 or its prerequisites. Do not enable alert destinations until the accountable owner approves the recipient and routing configuration. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is done.

- [ ] Task 1: collector-agent-and-secret-contract - pin and configure Alloy, finalize Environment-specific inputs, and reconcile the canonical role/profile contract
- [ ] Task 2: host-container-and-proxy-telemetry - collect resource/container signals and safe Nginx/app logs without secret-bearing fields
- [ ] Task 3: database-certificate-and-backup-signals - integrate the read-only PostgreSQL exporter and the spec 07/13 metric contracts
- [ ] Task 4: grafana-dashboards - deliver platform and reusable Environment/app dashboards with bounded labels
- [ ] Task 5: independent-uptime-probes - configure external HTTPS checks and prove collector/route failures are independent
- [ ] Task 6: alert-rules-and-approved-routing - implement OBS-03 rules and test delivery only to an approved route
- [ ] Task 7: ingestion-estimate-and-quota-review - estimate usage, confirm plan fit, and define the first-month measurement
- [ ] Task 8: verification-runbook-and-staging-acceptance - extend spec 05 checks, document operations, and record sanitized Staging evidence

The 85% disk/inode threshold, 21-day certificate threshold, and 8-hour backup threshold must remain consistent across the alert rules, verifier, dashboards, and runbook. If Q5 recipient/routing approval or Q10 plan fit is still missing, record that gate as blocked; do not mark alert delivery or Production readiness complete.
