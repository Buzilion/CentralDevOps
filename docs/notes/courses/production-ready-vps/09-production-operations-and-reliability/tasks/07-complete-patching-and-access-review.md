# Task 07 — Complete a patching, dependency, and access review

## Outcome

Produce an auditable maintenance record showing that supported components, urgent updates, reboot requirements, production credentials, and operator access have named owners and safe change paths.

## Prerequisites

- Complete Tasks 01–06 and review [Lesson 07 — Patching, dependency updates, and access reviews](../lessons/07-maintenance-patching-dependency-updates-and-access-reviews.md).
- Have an approved inventory of the host, application artifacts, container base images, database/proxy/runtime, CI workflows, automation dependencies, provider access, and secrets locations.

## Procedure

1. Inventory component name, current version/source, owner, update channel, support status, exposure, and next review date. Mark versions that cannot be determined.
2. Review pending OS security updates and reboot-required state. Categorize urgent vulnerabilities separately from routine updates; consult the relevant vendor/provider advisory.
3. Review application dependencies, base images, GitHub Actions and automation dependencies for stale, unsupported, or untrusted references. Record evidence; do not update production blindly as part of the inventory step.
4. Select one suitable update and follow the documented test, backup, maintenance, deployment, and post-update verification path. Schedule reboot only with tested access/recovery and expected-impact communication.
5. Review named users, SSH keys, sudo permissions, CI deployment secrets, registry and backup credentials, monitoring access, and provider-console access. Record owner, scope, expiry/rotation path, and last verification—not secret values.
6. Identify unused or overprivileged access for removal. Before rotation, list consumers and verify a replacement credential works; preserve tested administrative and recovery access until the change is confirmed.
7. Create tickets/actions for unsupported components, urgent patch gaps, access exceptions, and unverified reboot/rotation procedures with owner and target date.
8. Store the dated review and update the recurring maintenance calendar.

## Acceptance criteria

- [ ] Material OS, application, image, CI, automation, and infrastructure components have versions/sources or explicit unknowns.
- [ ] Pending security work and reboot requirements are reviewed with urgency and owner.
- [ ] At least one update has passed the documented verification path, or a clearly justified blocker is assigned.
- [ ] Access and credential inventory states owner, scope, and rotation/revocation procedure without recording secret values.
- [ ] Unused access is removed only after a replacement/recovery path is verified.
- [ ] Every unsupported or overdue item has an owner, due date, or documented risk acceptance.
- [ ] Review evidence is sanitized and retained outside the VPS.

## Deliverable

A dated **maintenance and access review record** plus prioritized update/access actions in the approved tracker.
