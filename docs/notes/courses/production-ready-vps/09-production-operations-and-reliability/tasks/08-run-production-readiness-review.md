# Task 08 — Run a production operations readiness review

## Outcome

Make a documented go/no-go decision on whether the VPS application can be operated safely, based on evidence from this subject and the preceding seven subjects.

## Prerequisites

- Complete Tasks 01–07 and review [Lesson 08 — Reliability exercises and continuous improvement](../lessons/08-reliability-exercises-and-continuous-improvement.md).
- Gather the operating contract, deployment and rollback evidence, health/restart test, failure matrix, capacity budget, backup/restore report, monitoring/alert evidence, maintenance/access review, and production checklist.

## Procedure

1. Appoint a reviewer other than the primary implementer where practical. Agree the service scope, review date, and whether the review is for a real production release or a learning environment.
2. Verify the service and access boundaries: SSH/admin recovery path, firewall exposure, secrets handling, public routes, private dependencies, and least-privilege deployment access.
3. Verify delivery evidence: pinned release identity, tests/build provenance, deployment approval, post-deploy checks, downtime expectation, rollback/forward-fix path, and migration/data compatibility.
4. Verify reliability evidence: restart and reboot test, persistent data, off-site backup and restore test, external availability check, alert delivery, logs/metrics freshness, capacity margin, and runbook access outside the VPS.
5. Verify maintenance and incident operations: named owners, escalation and decision authority, update cadence, access review, incident procedure, and recovery communication.
6. For each control, record **pass**, **fail**, or **not applicable with rationale**; cite a sanitized evidence location, owner, and review date. Do not mark undocumented assumptions as pass.
7. Classify blockers by user impact, exploitability, data-loss risk, and recovery difficulty. Assign each blocker an owner and due date. Record residual risks accepted by the authorized owner.
8. Make an explicit go/no-go recommendation. A no-go is a valid result. If go, define expiry/re-review triggers such as architecture, provider, database, credential, or monitoring changes.
9. Store the signed or attributable review outside the VPS and update the production checklist only for evidence that exists.

## Acceptance criteria

- [ ] Each required control has pass/fail/not-applicable status and a traceable, sanitized evidence reference.
- [ ] Reviews include all eight roadmap subjects and actual application dependencies rather than generic assumptions.
- [ ] Backup restore, external monitoring/alerting, reboot/restart, deployment rollback, and capacity are supported by exercises or test evidence.
- [ ] Critical blockers are not hidden by an overall score; each has an owner and due date.
- [ ] Residual risk and go/no-go decision are accepted by the named service owner.
- [ ] Runbooks and records are accessible without the VPS and contain no secrets or unnecessary personal data.
- [ ] Re-review triggers and date are defined; unresolved limitations remain visible.

## Deliverable

A dated **production operations readiness review** with evidence references, decision, blockers, accepted risks, action owners, and re-review triggers.
