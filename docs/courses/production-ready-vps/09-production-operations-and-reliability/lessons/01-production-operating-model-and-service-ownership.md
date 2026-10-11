# 01 — Production operating model, ownership, and service expectations

## Learning objectives

You can explain what it means to operate a production service, assign operational ownership, define service expectations that can be tested, and set a maintenance rhythm appropriate to a single VPS.

## Production is an operating responsibility

A service is not production-ready merely because it starts and returns a successful response. Production operation includes the entire period after deployment: observing behavior, applying changes, handling incidents, restoring service and data, controlling access, and keeping procedures current. The operator needs to know what is running, what depends on it, what can change it, and how to recover when normal assumptions fail.

Treat the service as a lifecycle:

```text
Prepare -> Release -> Verify -> Operate -> Maintain
   ^                                  |
   +---------- Recover / Improve -----+
```

Each transition needs evidence. A release has an identifiable version and a result. A recovery has a verified service outcome and a record of decisions. A maintenance action has a scope, owner, and way to check whether it worked. This is operational control, not paperwork for its own sake.

## Establish an operating contract

Write a short service contract before choosing alert thresholds or promising uptime. It should state:

- The service and environment covered, its users, business-critical operations, and service owner.
- The public access path and critical dependencies, including which dependencies are outside your control.
- Expected availability and maintenance communication, measured at the user-facing boundary where possible.
- What “healthy” means for essential requests, not just for an open port or running process.
- Support coverage, response expectations, escalation contacts, and who can authorize a risky change or accepted data loss.
- Recovery targets or known limits, based on the backup and restore evidence from Subject 07.
- Explicit exclusions and unknowns, including the single VPS as a failure boundary.

An **SLO** is an internal target for a measured service indicator over a stated window. It is not an availability guarantee unless there is a real commitment, measurement method, and consequence behind it. Do not advertise “high availability” when one VPS, one network path, or one provider account can stop the service. Honest limits help users and operators make decisions during maintenance and incidents.

## Assign ownership and decision rights

Every important operational activity needs a responsible person or role: deployments, VPS access, alerts, backups, restore approval, security updates, provider escalation, and public status communications. For a single-owner project, write down a backup contact or an explicit out-of-hours limitation. A procedure that assumes the original author is always available is a hidden dependency.

Distinguish who performs a procedure from who accepts its consequences. An operator may execute a database restore, but the service owner should authorize a restore that discards valid writes. A maintainer may schedule a reboot, but the owner should decide whether the expected interruption is acceptable. This avoids hurried, implicit decisions during an incident.

## Use a sustainable operations cadence

Build a small calendar rather than relying on memory:

| Cadence | Example work |
|---|---|
| Continuous | External availability checks, resource monitoring, alert delivery, automated backups |
| Per release | Review changes, validate health, observe error/latency behavior, verify rollback readiness |
| Routine (for example, weekly) | Review alerts, failed jobs, backup results, disk trends, and pending security updates |
| Scheduled (for example, monthly) | Apply planned maintenance, inspect access and credentials, review capacity and runbook accuracy |
| Periodic / after change | Restore exercise, incident or failure rehearsal, ownership and dependency review |

The exact frequency depends on risk, support capacity, update severity, provider policy, and available evidence. Assign an owner and record completion. A cadence is not a substitute for urgent action on an actively exploited vulnerability, a failing backup, or an imminent disk-full condition.

## Keep operations evidence useful and safe

Record release identifiers, timestamps, actions, results, approvals, and follow-ups. Do not store passwords, private keys, access tokens, customer records, or unredacted diagnostic payloads in a general runbook or exercise report. Put credentials in the approved secret store and document how an authorized operator retrieves them. Store essential procedures outside the VPS so that loss of the server does not erase the recovery instructions.

## Practical checkpoint

Complete [Task 01 — Define the operating contract and maintenance cadence](../tasks/01-define-operating-contract-and-maintenance-cadence.md) before treating any later task as an operational control.

## Knowledge check

1. Why is a successful deployment not proof of operational readiness?
2. What service claims become misleading when one VPS is a single point of failure?
3. Who should authorize a restore that may discard valid data?
4. Which operational documents must remain accessible if the VPS is lost?

## References

- [Google SRE Book — Embracing Risk](https://sre.google/sre-book/embracing-risk/)
- [Google SRE Book — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)
