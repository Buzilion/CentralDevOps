# 07 — Schema migrations, releases, and recoverable change

## Learning objectives

You can explain why restoring data is coupled to application and schema versions, plan a safe pre-change recovery point, and distinguish a deployment rollback from a database rollback.

## A database restore is not automatically a release rollback

An older application can fail against a newer schema; a newer application can fail against an older schema. A database restore also discards every valid write made after its recovery point. Therefore, “restore last night's database and redeploy the previous image” is not inherently safe. Recovery planning must identify the compatible pair of application release and schema/data state, and decide how post-backup writes will be handled.

Before each risky migration or release, identify:

- the exact image/source revision and migration set;
- the current schema and application version;
- the change's reversibility and expected lock/downtime behavior;
- the backup or snapshot to create and how to verify it;
- whether files and database state must be captured together;
- the procedure to stop writes, restore, replay, or forward-fix;
- how writes made after the recovery point are retained, reconciled, or explicitly lost;
- the service and data validation required before returning traffic.

Use the normal deployment mechanism and a staging copy for rehearsal. Confirm that the backup is outside the same failure boundary and that restore duration fits the change window. Do not treat a database backup as a substitute for testing migrations.

## Expand-and-contract migration pattern

When a schema change can be split, a compatibility-oriented approach reduces dependence on destructive rollback:

1. **Expand:** add the new schema elements in a backward-compatible way; deploy code that can tolerate old and new representations.
2. **Migrate:** backfill or transform data in bounded, repeatable batches; monitor progress and correctness.
3. **Switch:** move reads/writes to the new representation and validate behavior.
4. **Contract:** only after old code is no longer needed and data is verified, remove obsolete columns or formats in a later release.

This pattern is not possible for every change, and compatibility must be demonstrated for the actual application and its database-access layer (for example, an ORM that generates queries against the schema). For an irreversible migration, prefer a staged data transformation, an explicit maintenance window, a tested point-in-time restore, or a forward-fix plan. Never assume that rerunning a partially completed migration is safe; inspect migration transactionality and idempotency.

## Snapshot boundaries and write freeze

A pre-migration backup is useful only if it represents a consistent boundary. If the database and uploaded files change together, quiesce writes or use coordinated snapshots. Record when writes were stopped and resumed. For systems with continuous transaction logs, record the target replay time and preserve all required log segments. If a full restore is chosen, estimate the effect of losing valid changes after the snapshot and arrange for reconciliation or an approved loss decision.

For forward-only migrations, rollback may mean deploying a compatible code release while keeping the new schema, or applying a corrective migration. For destructive data transformation, rollback might require restoring and replaying accepted writes; it may be more reliable to repair forward. Document the decision before deployment.

## Preserve a versioned recovery set

For each production release, retain enough identifiers to associate the image digest/revision, database engine version, migration version, backup timestamp, and related files. Keep configuration needed for recovery separately protected. Do not retain secrets in a plain release manifest. Pin and verify restore tooling where practical; a major engine upgrade can change backup compatibility and restore procedures.

## Practical checkpoint

Complete [Task 06 — Rehearse a risky release and data-recovery decision](../tasks/06-rehearse-a-risky-release-and-data-recovery-decision.md) in staging or a disposable clone. Production migration rollback must not be improvised during an outage.

## Knowledge check

1. Why can restoring a database undo correct writes made after the backup?
2. What does expand-and-contract achieve for application/schema compatibility?
3. When may a forward-fix be safer than restoring an older database?
4. Which release and recovery identifiers should be recorded together?

## References

- [PostgreSQL documentation — Backup and Restore](https://www.postgresql.org/docs/current/backup.html)
- [GitHub Actions — Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
