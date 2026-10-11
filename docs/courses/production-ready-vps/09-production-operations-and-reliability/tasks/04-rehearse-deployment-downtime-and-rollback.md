# Task 04 — Rehearse deployment, downtime, and rollback

## Outcome

Prove the release procedure can deploy an identifiable version, detect a bad outcome, and recover through rollback or a documented forward-fix decision without assuming downtime-free behavior.

## Prerequisites

- Complete Tasks 01–03 and review [Lesson 04 — Safe deployments, downtime, and rollback](../lessons/04-safe-deployments-downtime-and-rollback.md).
- Have a non-production target or written approval for a bounded, reversible production change.
- Confirm backup/recovery status, active artifact identity, change approval, maintenance communication, and access to the prior release.

## Procedure

1. Select a representative release. Record source revision, immutable artifact identifier, currently deployed version, changed configuration/schema, expected user impact, and maintenance window.
2. Write preflight checks: tests/build result, required variables/secrets available without printing values, dependency and disk headroom, backup evidence for state changes, and rollback/forward-fix decision.
3. Define exact post-deploy gates: expected version, startup/readiness, key operation, external HTTPS path, logs/error/latency limits, observation duration, abort condition, and decision authority.
4. Deploy the release using the normal documented mechanism. Capture start/end time and actual service interruption from the user-facing boundary.
5. If safe, exercise a deliberate failed health gate on a test release or staging target. Follow the stop condition and rollback procedure. For a production deployment without a safe injected failure, rehearse the rollback in staging or as a tabletop and state the untested parts.
6. Verify the prior release or approved forward fix serves the key operation and external path. Confirm persistent data and background work are correct; do not infer that image rollback reverses migrations.
7. Record each decision, observed downtime, deviations, and unresolved state-compatibility concerns. Restore normal alerts and clean test artifacts.
8. Update the deployment runbook and assign follow-up owners.

## Acceptance criteria

- [ ] Active and candidate releases are unambiguously identifiable and retrievable.
- [ ] Preflight, post-deploy gates, abort conditions, and approval authority are documented.
- [ ] Actual downtime or non-downtime behavior is measured at the user-facing path.
- [ ] Rollback is tested or its untested portions and forward-fix alternatives are explicitly recorded.
- [ ] Schema/data compatibility and consequences of restore are considered.
- [ ] Recovery is verified with the critical application operation, fresh signals, and external route.
- [ ] Evidence is sanitized; alerts and temporary test configuration are restored.

## Deliverable

A dated **release and rollback rehearsal report** with release identities, timing, gates, decision log, verified outcome, downtime measurement, and corrective actions.
