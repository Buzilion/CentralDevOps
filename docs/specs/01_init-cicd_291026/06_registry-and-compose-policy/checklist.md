# Checklist for 01_init-cicd_291026/06_registry-and-compose-policy

> Implementation is blocked until every task in `01_foundation-and-access/checklist.md` and `03_host-bootstrap-and-hardening/checklist.md` is checked off.

- [ ] Task 1: policy-schemas - Define strict registry and app-manifest schemas with positive and negative fixtures
- [ ] Task 2: registry-integrity - Validate registry paths, global claims, manifest domains and inventory placements
- [ ] Task 3: capacity-control - Enforce per-host memory budgets from resolved inventory data
- [ ] Task 4: compose-policy - Render Compose and enforce the complete policy with regression fixtures
- [ ] Task 5: ci-gate - Add the required `registry-policy` check and operator runbook
- [ ] Task 6: policy-acceptance - Verify the full validation flow and record sanitized evidence

At each task close, add its sanitized `summaries/task-<n>-summary.md`. Do not create implementation summaries before the task is complete.
