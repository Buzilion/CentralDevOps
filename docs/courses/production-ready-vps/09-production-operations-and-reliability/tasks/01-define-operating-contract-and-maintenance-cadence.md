# Task 01 — Define the operating contract and maintenance cadence

## Outcome

Produce a concise, reviewed operating contract that states who operates the service, what users can expect, what is covered, and how routine maintenance and escalation are handled.

## Prerequisites

- Complete Subjects 01–08 and review [Lesson 01 — Production operating model, ownership, and service expectations](../lessons/01-production-operating-model-and-service-ownership.md).
- Inspect the deployed application and the previously documented runtime, deployment, backup, monitoring, and recovery procedures.

## Procedure

1. Name the service, environment, critical user-facing operations, service owner, operational contact, and backup/escalation contact. If a role has no available backup, state the support limitation.
2. Draw or link the actual request path and list critical dependencies, external owners, data stores, and known single points of failure.
3. Define what user-visible availability means, where it is measured, the reporting window, planned-maintenance treatment, and any agreed internal SLO. Label targets as provisional if evidence or owner agreement is missing.
4. Link the tested backup and recovery evidence. Record measured or estimated recovery limits and distinguish them from targets that have not yet been demonstrated.
5. State maintenance expectations, communication channel, support coverage, deployment authority, restore/data-loss approval, and provider escalation path.
6. Create a recurring maintenance calendar for update review, backup/alert review, access review, capacity review, and recovery/reliability exercises. Name an owner for each item.
7. Ask the service owner or another operator to review the document. Resolve contradictions with the existing production checklist and runbooks.
8. Store the sanitized contract and calendar outside the VPS in the approved documentation location.

## Acceptance criteria

- [ ] Service scope, user-critical operations, owner, contacts, and support limitations are explicit.
- [ ] Dependencies and known single points of failure are listed; a single VPS is not described as highly available.
- [ ] Availability language has a measurement boundary, time window, and planned-maintenance rule, or is explicitly marked as undecided.
- [ ] Recovery expectations are linked to evidence and distinguish tested results from unverified targets.
- [ ] Change, restore, and communication decision rights are clear.
- [ ] Recurring maintenance work has an owner and cadence.
- [ ] The document is sanitized, stored off-host, and reviewed by a second person where practical.

## Deliverable

A dated **operating contract and maintenance calendar** linked from the production runbook.
