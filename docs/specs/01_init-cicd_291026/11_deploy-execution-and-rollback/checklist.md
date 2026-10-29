# Checklist for 01_init-cicd_291026/11_deploy-execution-and-rollback

Implementation is blocked until every task in `04_docker-and-deploy-runtime/checklist.md`, `07_routing-and-tls/checklist.md`, `08_shared-database/checklist.md` and `10_deploy-authorization/checklist.md` is complete. Spec 09 is authored and must be completed before spec 10; spec 10 must be generated and completed before implementing spec 11. Complete the tasks below in order unless a task dependency explicitly permits otherwise. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is accepted.

- [ ] Task 1: deploy-job-and-approval-gate - Add the authorized deploy job, Environment approval boundary and per-app workflow scheduling
- [ ] Task 2: host-entrypoint-locking-and-audit - Implement the restricted host entrypoint, per-app locks and source-run audit correlation
- [ ] Task 3: release-transaction-preparation - Preserve previous state, integrate database provisioning and run optional release commands
- [ ] Task 4: health-check-and-automatic-rollback - Enforce the health timeout and safely restore the prior release or stop a failed first deploy
- [ ] Task 5: route-activation-and-smoke-test - Integrate spec 07 route activation, external HTTPS smoke test and Q8 behavior
- [ ] Task 6: deployment-records-and-run-summaries - Write secret-free host records and publish the central summary/result handoff
- [ ] Task 7: failure-runbook-and-staging-acceptance - Document operations and prove failure, locking, audit and secret-handling behavior on Staging
