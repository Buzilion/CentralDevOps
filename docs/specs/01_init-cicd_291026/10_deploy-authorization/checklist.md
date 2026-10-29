# Checklist for 01_init-cicd_291026/10_deploy-authorization

Implementation is blocked until every task in `02_dispatch-trust-proof/checklist.md`, `06_registry-and-compose-policy/checklist.md` and `09_app-build-and-provenance/checklist.md` is checked off. Complete the tasks below in order unless a task dependency explicitly permits otherwise. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is done.

- [ ] Task 1: dispatch-workflow-contract - Define the six-input `workflow_dispatch`, trusted App actor, main-branch guard and least-privilege job boundary
- [ ] Task 2: oidc-verifier - Verify GitHub's OIDC signature, claims, correlation metadata and exact request-byte audience with synthetic-key tests
- [ ] Task 3: registry-provenance-authorization - Derive the app, enforce refs/digest/SLSA provenance and resolve one target host per required group
- [ ] Task 4: replay-protection - Serialize authorization and reject a reused verified source `repository`/`run_id`/`run_attempt` before Environment selection
- [ ] Task 5: sealed-bundle-preflight - Decrypt safely after approval and validate archive, manifest, rendered Compose and exact runtime keys
- [ ] Task 6: workflow-environment-gate - Integrate authorization and the single Environment-bound preflight job; preserve the spec 11 handoff and spec 12 correlation
- [ ] Task 7: rejection-acceptance - Exercise positive and negative cases, verify no leakage or host access, and record sanitized evidence
