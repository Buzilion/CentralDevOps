# 01 — Data inventory, ownership, and recovery objectives

## Learning objectives

You can identify what must be recovered, distinguish authoritative data from rebuildable artifacts, assign an owner and recovery priority, and turn vague expectations such as “regular backups” into measurable Recovery Point Objectives (RPOs) and Recovery Time Objectives (RTOs).

## Start with the application, not a backup product

Backup design starts with the data the application actually creates and depends on. A source repository, an image registry, a Docker volume, and a database are not interchangeable copies of application state. Inspect the deployment and runtime contract established in the earlier course subjects: configuration, Compose mounts, service dependencies, scheduled jobs, upload paths, and database migration behavior. Read the application documentation and ask what is authoritative if two copies disagree.

Build a data inventory. Include at least:

| Data class | Questions to answer |
|---|---|
| Relational or document database | Which engine and version? Which database/schema? What is the supported consistent backup and restore method? Are transaction logs needed for point-in-time recovery? |
| User uploads and generated files | Where are they written? Can they be regenerated? Are names, permissions, metadata, and database references coupled to them? |
| Application configuration | Which values are in version control, which are environment-specific, and which contain secrets? Can a clean host recreate the configuration? |
| Secrets and encryption keys | Which services require them to decrypt or restore? Where is the recovery copy held, and who can access it? |
| Deployment and migration artifacts | Can the exact application release, schema migration, and backup tools be identified and retrieved? |
| External state | Does a managed database, object store, email provider, identity service, or another VPS hold part of the source of truth? What is that provider's recovery contract? |

For each item record its owner, source of truth, location, sensitivity, change rate, dependencies, retention requirement, and restoration order. Mark state as **durable**, **rebuildable**, **replicated elsewhere**, or **intentionally ephemeral**. “It is in Docker” does not answer this: container layers can be discarded, volumes can be deleted, and both can be lost with the host.

Avoid backing up everything indiscriminately. Caches and temporary files can waste storage and prolong recovery; omitting uploads or secrets may make a database restore unusable. Backups also create another copy of potentially sensitive data, so every included data class needs a protection and deletion policy.

## RPO: how much data can be lost?

The RPO is the maximum amount of recent data the service can afford to lose, expressed as the gap between a data-loss event and the newest usable recovery point before it. It is a business and product decision, not a property automatically granted by running a nightly job. A daily backup can imply nearly a day of data loss, and the actual gap can be longer if the last successful run failed or a restore point is corrupt.

Some systems can accept scheduled snapshots. Others need more frequent snapshots or database transaction-log archiving — for example PostgreSQL's write-ahead log (WAL) or MySQL's binary log (binlog) — to reconstruct a point in time. Continuous recovery is more complex: archive completeness, ordering, retention, compatible base backups, and a tested replay procedure are all required. Do not promise point-in-time recovery because logs are enabled; demonstrate that the required chain exists and replays.

## RTO: how long can recovery take?

The RTO is the maximum acceptable time from a defined outage or data-loss event to a validated service. It includes decision and access delays, obtaining a clean target, installing compatible tools, retrieving and decrypting data, restoring database and files, applying necessary configuration, validating the application, and routing traffic safely. A fast backup job does not establish a fast RTO.

Set objectives by data class and service priority if necessary. Record assumptions such as VPS provisioning time, backup size, network throughput, encryption-key availability, provider access, and staff availability. Measure a real restore; adjust the objectives or design when the evidence cannot meet them. Do not silently redefine a missed objective after the exercise.

## Source of truth and ordering

Related state may need to represent the same point in time. For example, a database row may point at an uploaded file. Restoring a newer database with older files can leave broken references; restoring newer files with an older database can expose orphaned or inconsistent content. Document the required ordering and consistency method across stores.

If an external provider is the source of truth, determine whether the VPS backup is needed at all, what the provider retains, how an export is recovered, and whether egress, quotas, or account access affect RTO. Provider replication is not the same as an independent historical backup: accidental deletion or corrupted writes may replicate too.

## Practical checkpoint

Complete [Task 01 — Inventory state and define measurable recovery objectives](../tasks/01-inventory-state-and-define-recovery-objectives.md). The output is a sanitized inventory and recovery contract, not a list of guessed backup commands.

## Knowledge check

1. Why is “backup every night” not a complete RPO statement?
2. Which steps between outage detection and application validation contribute to RTO?
3. Why might a database-only restore be unusable when the application also stores uploads?
4. Which data can be rebuilt safely, and what evidence supports that classification?
