# Checklist for 01_init-cicd_291026/12_app-deploy-request

Implementation is blocked until `10_deploy-authorization/checklist.md` and `11_deploy-execution-and-rollback/checklist.md` are complete. Continue in roadmap numeric order; drafting this spec does not waive specs 09–11. Complete the tasks below in order unless a task dependency explicitly permits otherwise. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is done.

- [ ] Task 1: request-action-contract - define the shared action interface, outputs, and fail-fast validation
- [ ] Task 2: sealed-bundle-and-size-guard - package and age-seal the three request files, handle key overlap, and enforce the payload decision
- [ ] Task 3: oidc-bound-dispatch - bind the exact request, create the dispatch App token, and dispatch CentralDevOps on a ref allowed by the requested Environment
- [ ] Task 4: central-run-polling - correlate the central run, propagate its result, and report a sanitized run URL
- [ ] Task 5: app-deploy-workflow - render runtime configuration safely and add the two-input manual app `deploy.yml`
- [ ] Task 6: release-and-rollback-runbook - document build, Staging verification, Production approval, and rollback by digest
- [ ] Task 7: app-request-acceptance - prove the Staging request, payload rejection, secret handling, and digest rollback end to end
