# Task 06 — Verify a release and rehearse rollback

## Outcome

Prove that the delivery workflow detects an unhealthy release, preserves the failed-run status, and can restore the last-known-good image and service when safe to do so.

## Prerequisites

- Complete Task 05 and have a known-good release available by digest.
- Read [Lesson 07 — Post-deployment verification and rollback](../lessons/07-post-deployment-verification-and-rollback.md).
- Use a staging or disposable target for the deliberate failure rehearsal. Do not inject a broken image or destructive migration into production.

## Procedure

1. Define the application's real readiness check, expected route/status, timeout, retry interval, and maximum wait from the release contract. Verify the check reaches the intended service rather than a stale endpoint or a generic reverse-proxy response.
2. Record the currently running image digest and relevant non-secret runtime configuration. Confirm the previous image is retained and the VPS can pull it.
3. Deploy a known-good candidate to staging. Verify the running digest, container health/readiness, application-level request, required dependency behavior, and logs. Record the elapsed time and results.
4. Trigger a controlled failure that is safe and reversible (for example, a staging-only candidate with a known failing readiness response). Do not remove volumes or alter production data.
5. Confirm the deployment workflow times out/fails clearly, invokes only the documented recovery action, restores the prior digest if automatic rollback is safe, and runs the readiness check again. The overall release run must remain failed even when recovery succeeds.
6. Verify that a schema migration, persistent-data incompatibility, or uncertain state stops for operator review instead of blindly rolling back application or database state.
7. Document manual recovery steps and the decision owner. After the rehearsal passes, promote only a reviewed release through the protected production path.

## Acceptance criteria

- [ ] Success requires the expected immutable digest and a meaningful application readiness check.
- [ ] The check has bounded retries/timeouts and does not convert persistent failure into success.
- [ ] A controlled failed candidate is detected and the run remains failed.
- [ ] The prior digest can be restored and passes readiness checks in the safe test target.
- [ ] Persistent data and database schema are untouched by the rollback rehearsal.
- [ ] Uncertain migration/data state triggers a safe stop and documented human decision.
- [ ] Evidence records before/after digests, failure detection, rollback outcome, and time to recovery.

## Deliverable

A sanitized deployment and rollback runbook plus staging rehearsal record. Include the tested commands/controls by name, success/failure evidence, rollback time, and exceptions; omit secrets, raw logs, and identifying host details.
