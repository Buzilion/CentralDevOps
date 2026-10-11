# Task 01 — Inventory state and define measurable recovery objectives

## Outcome

Create a sanitized, application-specific data inventory and a recovery contract that names what must be recovered, from where, by which method, and within what data-loss and downtime limits.

## Prerequisites

- Read [Lesson 01 — Data inventory, ownership, and recovery objectives](../lessons/01-data-inventory-ownership-and-recovery-objectives.md).
- Have the application runtime contract from [Docker Task 01](../../03-docker-and-container-operations/tasks/01-discover-and-document-the-application-runtime-contract.md) and release design from [CI/CD Task 01](../../05-ci-cd-with-github-actions/tasks/01-inspect-the-application-and-define-the-release-contract.md), or perform equivalent repository inspection.
- Read [Docker Task 05](../../03-docker-and-container-operations/tasks/05-prove-data-persistence-and-private-service-connectivity.md) for the distinction between container persistence and backup.

## Procedure

1. Inspect the actual release configuration, application documentation, database configuration, container mounts, external services, background jobs, and upload/generated-file paths. Use a staging or read-only inspection path where possible; do not print secret values.
2. Trace representative writes to their real destination. For each data class, record its owner, source of truth, location/service, change rate, sensitivity, dependencies, retention need, and whether it is durable, rebuildable, external, or intentionally ephemeral.
3. Identify coupled state. Record which database rows refer to files, what configuration/secrets are required to interpret data, and the order in which components must be recovered.
4. For each important class, select a candidate backup and restore method supported by its owner/engine. Record consistency guarantees, limitations, restore prerequisites, and unknowns. Do not mark an unknown guarantee as adequate.
5. With the application owner, set an RPO and RTO in hours/minutes for each recovery priority. State the outage start and “service restored” definitions used for RTO, and whether rebuilding/provisioning time is included.
6. Estimate size, growth, backup duration, transfer time, and restore time using available measurements. Compare the design with each RPO/RTO; mark objectives that are not yet demonstrated.
7. Store the inventory in an access-controlled location. Sanitize evidence: omit credentials, real record contents, secrets, private keys, and unnecessary host/provider identifiers.

## Acceptance criteria

- [ ] Every persistent path and external source of truth is listed, or an explicit evidence-based statement says the application has no durable state on the VPS.
- [ ] Each data class has an owner, classification, dependencies, candidate capture/restore method, and consistency note.
- [ ] Database and related file consistency requirements are documented.
- [ ] RPO and RTO are numeric, have a defined measurement boundary, and are approved by the appropriate owner.
- [ ] Backup, restore, storage, and credential unknowns are recorded rather than guessed.
- [ ] The inventory contains no secret values or application data.

## Deliverable

A dated, sanitized **data inventory and recovery contract**. Revisit it whenever storage paths, database engines, data sensitivity, or recovery requirements change.
