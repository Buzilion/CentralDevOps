# Task 03 — Build a failure diagnosis matrix

## Outcome

Give operators an evidence-first map from common symptoms to safe checks, likely failure boundaries, controlled mitigations, escalation, and recovery verification.

## Prerequisites

- Complete Tasks 01–02 and review [Lesson 03 — Failure diagnosis and dependency resilience](../lessons/03-failure-diagnosis-and-dependency-resilience.md).
- Have access to the external availability check, dashboard, logs, deploy history, and provider status/recovery path.

## Procedure

1. Select at least six realistic scenarios from the actual architecture, including public HTTP/TLS failure, application crash/restart loop, database or critical dependency unavailable, high memory/CPU, disk or inode pressure, failed deployment, and stale/missing telemetry.
2. For each scenario, record the user-visible symptom, first verification step, relevant timestamped signals/logs, likely boundary, and evidence that would confirm or reject the hypothesis.
3. Specify safe read-only checks first. Identify actions that change state, require approval, may destroy evidence, or risk data loss.
4. Define a lowest-risk mitigation and explicit stop/escalation condition for each scenario. Include rollback/forward-fix/restore decision points where appropriate.
5. State the user-facing recovery criterion and which fresh independent signal proves it. Include monitoring or provider failure fallbacks.
6. Conduct a tabletop walk-through with another operator or, if unavailable, record a self-review against each step. Then exercise one non-destructive or staging scenario.
7. Sanitize the document and link it from the operational runbook; add missing signals or access requirements as tracked actions.

## Acceptance criteria

- [ ] At least six scenarios cover application, network/proxy, dependency, host capacity, deployment, and telemetry boundaries.
- [ ] Each entry separates observed facts from hypotheses and uses timestamp-correlated evidence.
- [ ] Read-only checks precede state-changing actions, with risks and approvals identified.
- [ ] Each scenario names a mitigation, escalation/stop condition, and user-visible recovery check.
- [ ] The matrix includes a path for monitoring or VPS unavailability.
- [ ] At least one scenario was safely walked through; gaps have owners and due dates.
- [ ] No credentials, raw customer data, or destructive unguarded commands are included.

## Deliverable

A concise **failure diagnosis matrix** linked from the service runbook, with dated exercise notes and assigned follow-ups.
