# Task 06 — Rehearse a risky release and data-recovery decision

## Outcome

Prove in staging or a disposable clone that an application release and schema/data migration have an understood recovery path, including the treatment of writes made after a recovery point.

## Prerequisites

- Complete [Task 05 — Restore into an isolated environment and measure recovery](05-restore-into-an-isolated-environment-and-measure-recovery.md).
- Read [Lesson 07 — Schema migrations, releases, and recoverable change](../lessons/07-schema-migrations-releases-and-recoverable-change.md).
- Have a staging environment and a representative migration/release procedure. Do not rehearse destructive migration steps on live production data.

## Procedure

1. Select a real or representative schema/data migration. Record the previous and candidate application image/revision, database engine version, schema version, migration order, and affected data classes.
2. Write a pre-change decision record: expected downtime/locks, whether the migration is reversible, compatibility of both app versions, backup/snapshot method, consistency boundary, and how post-backup writes will be retained or reconciled.
3. Restore a known backup into staging using Task 05's isolation controls. Verify the previous application release works before applying the migration.
4. Run the migration and candidate application release using the normal deployment path. Validate expected schema/data and representative app behavior. If the migration supports expand-and-contract, exercise the compatible intermediate state where practical.
5. Simulate a failed release using a safe test failure (for example, make the candidate app fail its health check) without damaging the source backup. Exercise the documented response: compatible code rollback, corrective migration, or restore to a separate target.
6. Decide explicitly what happens to test writes made after the backup. Demonstrate the planned replay, reconciliation, or approved loss path; do not silently discard writes while claiming a no-loss rollback.
7. Record actual recovery steps, elapsed times, compatibility issues, and any point at which an operator had to improvise. Update the release/recovery decision record.
8. Clean up the disposable environment under the data-handling policy.

## Acceptance criteria

- [ ] Exact old/new app, engine, schema, and backup identifiers are recorded.
- [ ] Migration compatibility and reversibility are demonstrated or explicitly marked unavailable.
- [ ] The selected backup represents the needed database/files consistency boundary.
- [ ] A controlled candidate failure is handled without altering production.
- [ ] The plan for writes after the restore point is explicit and demonstrated or accepted as a measured limitation.
- [ ] Recovery does not assume application rollback also reverses database changes.
- [ ] Procedures and evidence contain no secrets or real user data.

## Deliverable

A sanitized **release recovery rehearsal record** with migration contract, compatible app/schema versions, tested failure response, treatment of post-backup writes, timing, and follow-up actions.
