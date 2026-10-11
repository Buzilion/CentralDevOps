# 07 — Post-deployment verification and rollback

## Learning objectives

You can define measurable deployment success, distinguish process health from user-visible service health, and rehearse rollback without treating data migrations as automatically reversible.

## Define success before the run

A deploy job is not successful merely because SSH connected, an image was pulled, or a container entered the running state. Define checks tied to the application's release contract:

1. The target host applied the expected image digest and Compose configuration.
2. The application process is running and its readiness/health check is healthy.
3. A local request through the service's intended route returns the expected status and, where useful, validates a release/build identifier.
4. Required dependencies are available and application logs show no immediate startup or migration failure.
5. An external uptime check confirms the public route after DNS and reverse proxy are in place.

Keep checks bounded by explicit timeouts and retries. A retry can handle normal startup delay; it must not hide a persistent failure. Fail with sanitized context that helps an operator diagnose the stage without revealing configuration or credentials. Do not declare success if the check is skipped, unreachable, or checking the wrong host/path.

Health endpoints have different meanings. A **liveness** check answers whether the process should be restarted; a **readiness** check answers whether it can safely receive traffic. An endpoint that returns success without checking needed dependencies may not establish useful readiness. Use the existing application contract or record a required application change.

## Design rollback around immutable releases

For an image-based deployment, record the last-known-good digest before changing the running service. A rollback should select that exact digest and restore the compatible runtime configuration, then repeat the same readiness checks. Keep the prior image available in the registry and preserve the configuration necessary to run it. A human-readable tag may have moved; the digest is the safer rollback identity.

Rollback is not necessarily restoring the whole system. A previous application version may not understand a database schema changed by the new version. Plan migrations using backward-compatible expand/contract steps where possible:

1. Add schema in a way the old and new application versions can both tolerate.
2. Deploy code that can use the new schema while old fields remain.
3. Migrate data with verification and an explicit recovery plan.
4. Remove obsolete schema only in a later release after it is no longer needed.

Never automatically reverse a destructive or data-changing migration just because an HTTP probe failed. Stop, preserve evidence and data, and use the documented operator decision. A rollback command should not delete persistent volumes or run broad cleanup.

## Rehearse failure safely

First rehearse in staging or with a harmless test release. Verify a healthy deployment, a deliberately unhealthy release, detection of failure, restoration of the previous digest, and a second successful health check. Confirm the workflow reports failure even if the recovery action restores service. A failed release that was automatically rolled back is still a failed release and should not be reported as green.

For production, define the decision owner, maximum detection time, rollback trigger, communication path, and any manual migration/data steps. If automated rollback can worsen a stateful failure, stop automatically after detecting the unhealthy deployment and request operator action instead.

## Practical checkpoint

Produce a runbook and run a controlled staging rehearsal. Capture sanitized before/after digests, health-check results, elapsed time, rollback result, and any limits. Complete [Task 06 — Verify a release and rehearse rollback](../tasks/06-verify-a-release-and-rehearse-rollback.md).

## Knowledge check

1. Why can restoring the previous container image fail to restore service?
2. Which conditions should cause the deploy job to fail rather than retry indefinitely?
3. Why should a successful rollback still leave the release workflow failed?
4. How do liveness and readiness answer different operational questions?

## References

- [Docker Compose: Services and health checks](https://docs.docker.com/reference/compose-file/services/)
- [GitHub Actions: Workflow commands and job status](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/using-conditions-to-control-job-execution)
