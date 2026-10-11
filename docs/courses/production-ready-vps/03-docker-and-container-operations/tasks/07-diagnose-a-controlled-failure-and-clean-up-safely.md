# Task 07 — Diagnose a controlled failure and clean up safely

## Outcome

Use container and host evidence to diagnose a reversible test failure, restore normal operation, and remove only explicitly disposable Docker resources while preserving application data and rollback capability.

## Prerequisites

- Read [Lesson 07 — Releases, rollback, troubleshooting, and cleanup](../lessons/07-releases-rollback-troubleshooting-and-cleanup.md).
- Completed Tasks 04–06 with a known-good Compose project and a retained rollback image.
- Use a non-production test service or approved maintenance window. Never inject failure into a critical production service or alter data to simulate an incident.

## Procedure

1. Record the Compose project name, current image reference, container IDs, health status, volume names, listener inventory, and recent logs. Confirm a recovery route and a known-good release.
2. In a disposable learning service only, create a bounded/reversible failure such as starting with an intentionally invalid non-secret configuration value. Do not change the production application's database, credentials, firewall, or host startup configuration.
3. Observe and record the behavior using `docker compose ps`, `docker inspect`, `docker compose logs --tail=100 SERVICE`, `docker events --since 10m`, and `docker stats --no-stream`. Redact secrets and identifying values.
4. Classify the symptom: process exit, failed health check, failed dependency path, host port/listener issue, or resource/disk problem. Explain which layer the evidence implicates and what evidence rules out other layers.
5. Restore the valid configuration or previous known-good image; apply the documented Compose operation. Confirm health and the application smoke test pass again.
6. Inventory Docker usage with `docker system df`, `docker image ls`, `docker container ls --all`, `docker network ls`, and `docker volume ls`. Identify exact disposable test objects by name/ID.
7. Remove only the confirmed disposable test container/image/network/volume. Before any volume removal, inspect its name and mounts and verify it contains no required data. Do not run broad prune commands as routine cleanup.
8. Re-run health, listener, and storage checks. Record whether the retained rollback image and required named volumes are still present.

## Acceptance criteria

- [ ] The failure was injected only into a disposable test service and was fully reversible.
- [ ] The diagnosis cites observed evidence and identifies the failure layer rather than relying on a blind restart.
- [ ] The service is restored to its known-good version and passes its acceptance check.
- [ ] No required volume, production data, or rollback image was removed.
- [ ] Every cleanup target was individually identified before removal.
- [ ] No broad `docker system prune`, `docker volume prune`, or `down -v` was used.
- [ ] Post-cleanup service health, host listeners, and disk/storage state are recorded.
- [ ] Diagnostic evidence is sanitized of secrets and identifying details.

## Deliverable

A private incident-drill record containing symptom, timeline, evidence sources, failure-layer reasoning, corrective action, health verification, cleanup targets, and preserved data/release inventory. Keep the failure-injection details scoped to this exercise; do not create an unsafe production change.
