# 06 — Incident response, decision-making, and operational runbooks

## Learning objectives

You can organize a proportionate incident response, establish impact and ownership, communicate and record decisions, use safe runbooks, and close an incident with verified recovery and useful follow-up.

## Declare and scope an incident

An incident is an unplanned event that materially affects or threatens service, data, security, or the ability to operate. Use severity levels to direct attention, not to grade people. Define examples appropriate to the service: a complete public outage, loss of a critical business operation, suspected data exposure, growing capacity risk, and a non-user-impacting warning should not all page the same response.

At the start, establish:

- Incident lead and technical operator; one person may hold both roles on a small service, but state that explicitly.
- Start time, impact, affected paths/users, current status, and what is not yet known.
- A communication channel and update cadence appropriate to severity.
- Decision authority for rollback, data restore, traffic changes, provider escalation, and external communication.
- Safety boundaries and evidence that must be preserved.

Do not delay a needed mitigation while seeking perfect certainty, but state the evidence and uncertainty behind it. Avoid parallel uncoordinated changes. Record a concise timeline with who did what, when, why, and the result.

## Follow a safe response loop

Use a repeatable loop:

1. **Assess:** verify user impact and whether the signal is current.
2. **Stabilize:** reduce immediate harm with the lowest-risk effective action.
3. **Investigate:** compare changes, public checks, application state, dependencies, host pressure, and logs.
4. **Decide:** choose restart, rollback, forward fix, failover (if it exists), or restore; identify data/security consequences.
5. **Recover:** make the approved change and validate the real user operation.
6. **Communicate:** provide factual status, next update, and limitations without speculation or sensitive detail.
7. **Close and learn:** state recovery evidence, remaining risk, owners, and due dates for corrective work.

If compromise is suspected, treat the affected host and credentials as untrusted. Preserve evidence as required by the response policy, contain access, use a clean recovery path, and avoid restoring potentially compromised artifacts blindly. Coordinate legal, privacy, or provider obligations with the responsible owner.

## Make runbooks executable by another person

A useful runbook begins with its scope, owner, last-reviewed date, access prerequisites, and expected healthy result. Each action should include:

- When to use it and a safe first check.
- The exact command or user-interface path for the deployed stack, with placeholders clearly marked.
- Expected output and what an unexpected result means.
- Whether the step changes production, its risks, and any approval/confirmation required.
- How to stop or reverse it, and how to prove recovery.
- Links to deployment, backup/restore, dashboard, log, provider-status, and escalation material.

Do not include secret values, instructions to blindly delete state, or copy-pasted commands that conceal destructive flags. Commands must match the actual host and application versions. Store the runbook outside the VPS and ensure the authorized operator can retrieve required credentials from the approved secret system.

## Recover service and retain evidence

Recovery is not established by “the command succeeded” or “the alert cleared.” Confirm the affected user journey, fresh monitoring samples, expected release/configuration, dependency behavior, and stability over an appropriate observation interval. Record actual detection, acknowledgment, mitigation, and recovery times when available. Preserve sanitized release IDs, event times, and relevant metrics/log references. Avoid copying raw personal data or secrets into incident notes.

## Learn without blame

A blameless review focuses on system conditions, missing safeguards, confusing procedures, and information available at the time. It does not remove accountability for corrective action. Select a small number of changes that reduce recurrence or impact, assign owners and due dates, and verify closure. Repeated incidents with uncompleted actions indicate a prioritization or ownership problem.

## Practical checkpoint

Complete [Task 06 — Practice incident response and update runbooks](../tasks/06-practice-incident-response-and-update-runbooks.md).

## Knowledge check

1. Why should incident severity direct response rather than assign blame?
2. Who approves a restore that may lose valid writes?
3. What evidence proves recovery beyond an alert clearing?
4. What changes to the response process if host compromise is suspected?

## References

- [Google SRE Book — Managing Incidents](https://sre.google/sre-book/managing-incidents/)
- [Google SRE Book — Postmortem Culture: Learning from Failure](https://sre.google/sre-book/postmortem-culture/)
- [CISA — Incident Response](https://www.cisa.gov/topics/cyber-threats-and-advisories/incident-detection-response)
