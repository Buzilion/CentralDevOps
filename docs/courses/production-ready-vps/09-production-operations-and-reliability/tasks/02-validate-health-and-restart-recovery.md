# Task 02 — Validate health checks and restart recovery

## Outcome

Demonstrate which health checks govern startup, process liveness, readiness, and external availability, and prove the configured process recovery behavior after a safe test failure and planned host restart.

## Prerequisites

- Complete Task 01 and review [Lesson 02 — Health checks, restart behavior, and process supervision](../lessons/02-health-checks-restart-behavior-and-process-supervision.md).
- Identify the actual supervisor (for example, Docker, systemd, or both), the health-check implementation, and a safe test environment or approved maintenance window.

## Procedure

1. Inventory each health signal: endpoint/command, consumer, cadence, timeout, failure threshold, dependency coverage, information returned, and expected action. Mark any unknowns.
2. Verify that startup delays cannot cause a restart loop, that liveness does not depend unnecessarily on remote services, and that readiness reports when the service cannot accept its required traffic.
3. Confirm public health output does not expose internal details. Review endpoint authentication/routing and check that frequent probes do not create material load.
4. Record the active release, health, external user path, persistent-data status, and current alert state before testing.
5. In a test environment, cause a controlled application process exit. Observe supervisor behavior, restart count, logs, health transition, and recovery. Confirm that the public/application operation succeeds afterward.
6. In a maintenance window with a working provider-console/recovery path, verify host reboot behavior. Confirm required services start, mounted state and secrets are present, checks become healthy, and the external path works. If reboot testing is not safe, validate on a disposable host and document the gap.
7. Simulate or use a test dependency outage if supported. Verify expected readiness/degraded behavior, bounded timeouts/retries, and that the app does not create a restart storm.
8. Restore normal state, confirm alerts and checks are active, and record deviations, owners, and due dates.

## Acceptance criteria

- [ ] Startup, liveness, readiness, and external availability have documented distinct semantics.
- [ ] Probe timeouts, cadence, dependencies, and failure actions are bounded and verified.
- [ ] Health output does not leak secrets or sensitive internal diagnostics.
- [ ] Controlled process-exit results match the intended restart policy and no restart storm occurs.
- [ ] Host reboot or an explicitly documented equivalent test proves boot recovery, persistence, and public service restoration.
- [ ] A representative user-facing request succeeds after recovery; a green process status alone is not accepted.
- [ ] Test state is cleaned up and any gaps have an owner.

## Deliverable

A sanitized **health and recovery test record** containing the check inventory, test timestamps, release, observed state transitions, verification results, and open actions.
