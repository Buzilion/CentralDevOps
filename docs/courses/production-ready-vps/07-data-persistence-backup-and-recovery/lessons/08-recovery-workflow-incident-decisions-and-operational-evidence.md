# 08 — Recovery workflow, incident decisions, and operational evidence

## Learning objectives

You can choose a recovery response based on the failure, protect evidence and unaffected copies, coordinate recovery decisions, and leave an auditable runbook that another operator can execute safely.

## Identify the failure before selecting a restore point

Different incidents need different responses. A stopped container may need a restart, not a database restore. Disk failure may require a clean host and a recent copy. Accidental deletion requires a point before the deletion, while a corrupted or malicious write requires a point before corruption began. Restoring too early can discard valid data; restoring too late can reintroduce the problem.

For suspected compromise or ransomware, treat production credentials and the host as untrusted. Do not reconnect a recovered copy to a compromised network or let the affected host overwrite backups. Preserve relevant logs and evidence according to the incident process. Use a clean recovery target, rotate credentials as appropriate, and establish how the compromise will be contained before returning service. A backup is not a security-clean image of the application host.

Choose among:

- **Repair/restart:** preserve data and restore the service when state is intact.
- **Restore a database or files:** use when a particular state store is damaged or deleted, after assessing consistency and dependent data.
- **Point-in-time recovery:** use when a precise pre-incident database state is required and the log chain is verified.
- **Full environment rebuild:** use when the host or its trust boundary is lost; restore application state to a clean host and redeploy known artifacts.
- **Forward-fix and reconciliation:** use when restoring would lose important valid writes or replay the incident.

Record the incident time, affected components, candidate restore points, data-loss consequences, service impact, and person authorized to accept those consequences. State assumptions and escalate when evidence is inadequate.

## Use a repeatable recovery sequence

The runbook should make each decision and stop condition clear:

1. Declare incident lead and recovery owner; record times and scope.
2. Preserve unaffected backup copies and evidence; restrict unsafe credentials or systems.
3. Identify the last known-good, usable recovery point and confirm its key, dependencies, and integrity.
4. Select the compatible application release and recovery target; confirm capacity, network isolation, and required access.
5. Restore components in the documented dependency order; capture command results without secret values.
6. Validate at storage, application, and business-flow levels against prewritten criteria.
7. Decide whether to accept/reconcile changes since the restore point; obtain approval for any expected data loss.
8. Reconnect service through a deliberate traffic change, watch for errors, and preserve the pre-recovery environment until acceptance.
9. Record actual RPO/RTO, deviations, follow-up actions, and secure cleanup.

Keep the runbook in version control or another durable, accessible location that does not depend on the failed VPS. Store a copy of the recovery procedure and access path away from the server; avoid putting credentials or encryption keys directly into the document.

## Evidence and improvement

Useful evidence is timestamped, sanitized, reproducible, and tied to an expected result. Record tool and engine versions, selected backup ID/time, checksums or integrity-check result, restored application release, validation outcomes, measured recovery times, and unresolved limitations. Redact hostnames, IP addresses, user identifiers, database names if sensitive, tokens, connection strings, and sample record contents.

After each drill or incident, identify the first point where the procedure diverged from the plan. Assign a corrective action and owner—such as reducing restore time, adding a missing role export, protecting a key-recovery path, or clarifying who approves data loss. A recovery runbook that nobody has executed becomes stale.

## Practical checkpoint

Consolidate and exercise the procedure in [Task 07 — Publish and exercise the application recovery runbook](../tasks/07-publish-and-exercise-the-application-recovery-runbook.md).

## Knowledge check

1. Why can restoring the most recent backup be wrong after data corruption?
2. What should change if the VPS itself may be compromised?
3. Which person or role should approve an explicitly accepted data-loss window?
4. What makes recovery evidence safe and useful to another operator?

## References

- [NIST SP 800-34 Rev. 1 — Contingency Planning Guide](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final)
- [CISA — StopRansomware Guide](https://www.cisa.gov/stopransomware/ransomware-guide)
