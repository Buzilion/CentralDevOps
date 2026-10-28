# 04 — Safe deployments, downtime, and rollback

## Learning objectives

You can plan a release around its user impact and state changes, select a deployment strategy justified by the topology, gate traffic on verified health, and decide when rollback is safe versus when forward repair is required.

## A deployment is a change to a running system

A release changes more than application files. It can alter runtime configuration, secrets, database schema, network rules, background jobs, cache formats, or persistent data. Identify the full change set and its compatibility requirements before deployment. Use an immutable, identifiable artifact (such as a versioned image digest or release identifier) rather than an ambiguous mutable tag. Record the currently deployed version and preserve the means to retrieve it.

A safe release plan states:

- What changes and which components/users can be affected.
- Preconditions: passing tests, artifact identity, configuration and secret availability, disk headroom, backup status when data changes, and dependency availability.
- The expected interruption, maintenance communication, deployment owner, and allowed window.
- The exact health criteria, observation interval, abort condition, and decision authority.
- The rollback or forward-fix path, including data compatibility and artifact access.

## Choose a strategy honestly

- **Stop-and-replace:** stop the old process, start the new one, then verify. This is simple and may be appropriate when a brief interruption is acceptable. State and measure the interruption.
- **Rolling update:** replace instances incrementally while at least one compatible healthy instance serves traffic. This requires more than one usable instance and a routing/supervision mechanism that removes unhealthy instances.
- **Blue-green:** run old and new versions separately and switch traffic after validation. It needs resources for both versions, a controlled traffic switch, compatible state changes, and a tested cleanup/rollback plan.

On a single small VPS, rolling or blue-green may not be worthwhile or possible. Two containers do not create high availability if both share the same host, storage, network, and power. Do not describe a replacement deployment as zero-downtime unless the public path and representative user operation have been measured and prove that claim.

## Order checks around the change

Before deployment, capture the active release, key health signals, current error/latency baseline, disk and memory headroom, backup/recovery status when relevant, and any active incident. Validate configuration without printing secrets. Confirm the prior artifact and recovery instructions are accessible. Make one bounded change at a time where practical.

After deploying, confirm the expected release is actually serving. Check startup completion, readiness, representative application behavior, dependency connectivity, logs, restarts, and external HTTPS behavior. Observe for a defined period sufficient to cover important background jobs or traffic patterns. Stop or roll back when a pre-agreed threshold is exceeded rather than improvising under pressure.

## Rollback is a data and compatibility decision

Rollback may be unsafe after an incompatible database migration, irreversible data transformation, external side effect, or secret/configuration rotation. Use expand-and-contract schema changes where appropriate: add compatible fields first, deploy code that can use both forms, migrate data, and remove old fields only after old code is no longer needed. Test this plan against the actual database and migration tooling.

When reverting application code cannot safely revert the state, choose a forward fix, restore, or reconciliation plan. A restore can discard valid post-backup writes. Require the service owner to accept that data-loss window. Keep the old and new artifacts, migration output, timestamps, and decision rationale until the release is accepted and recovery risk is understood.

## Verify user recovery, not only command success

A successful deployment command proves only that the command returned success. Verify the deployed identifier, application operation, external route, logs/metrics, and stable behavior. Confirm that alerts return to normal because measurements recovered—not because telemetry stopped. Record deployment duration, observed interruption, failed checks, actions, and any follow-up. Avoid exposing credentials or customer data in release evidence.

## Practical checkpoint

Complete [Task 04 — Rehearse deployment, downtime, and rollback](../tasks/04-rehearse-deployment-downtime-and-rollback.md) against a non-production target or a specifically approved, reversible production change.

## Knowledge check

1. What topology is required for a rolling update to keep serving traffic?
2. Why might reverting the application image be unsafe after a schema migration?
3. Which pre-deployment facts should be recorded to make rollback meaningful?
4. What evidence proves users recovered after the release?

## References

- [Google SRE Book — Release Engineering](https://sre.google/sre-book/release-engineering/)
- [Google SRE Workbook — Canarying Releases](https://sre.google/workbook/canarying-releases/)
- [Docker Docs — Compose in production](https://docs.docker.com/compose/how-tos/production/)
