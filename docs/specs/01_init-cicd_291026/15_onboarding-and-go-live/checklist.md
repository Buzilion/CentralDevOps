# Checklist for 01_init-cicd_291026/15_onboarding-and-go-live

Implementation is blocked until every checklist for specs 01-14 is complete. Continue in roadmap numeric order; drafting this spec does not authorize implementation or Production deployment. Complete the tasks below in order. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is done.

- [ ] Task 1: production-approval-model - resolve Q6 and verify the CentralDevOps Production reviewer handoff
- [ ] Task 2: onboarding-contract-and-guide - document the app contract, ownership, database migrations, and onboarding flow
- [ ] Task 3: second-app-onboarding-proof - onboard a second disposable app through Staging without CentralDevOps workflow edits
- [ ] Task 4: credential-rotation-runbook - document SEC-16 rotation procedures and safe rollback
- [ ] Task 5: staging-rotation-rehearsals - rehearse all mandatory rotations without a deployment outage
- [ ] Task 6: fourth-app-capacity-review - prepare the review record and complete it when the fourth-app trigger is reached
- [ ] Task 7: production-go-live-gate-record - verify and record all five parent PRD go-live gates
- [ ] Task 8: onboarding-and-go-live-acceptance - complete the second-app flow and Production acceptance only after all gates pass

Production must remain blocked if any gate in Task 7 is `FAIL`, `BLOCKED`, or missing. A capacity review not yet triggered because fewer than four distinct apps exist must be recorded as such; it must not be represented as a completed REG-12 review.
