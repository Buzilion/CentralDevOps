# Task 8: Verification, runbook, and Staging acceptance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Tasks 1 to 7 |
| Needs | Completed spec 05/13 contracts, Staging host/routes/backups, approved alert route, and one month of Staging usage |
| Summary | Write `summaries/task-8-summary.md` when this task closes |

## Goal

Extend the established read-only verifier, document safe operations, and prove end-to-end observability on Staging without exposing secrets or disrupting Production.

## Relevant files or references

- `roles/monitoring_agent/tasks/verify.yml`
- `playbooks/verify.yml`
- `docs/runbooks/observability-and-alerting.md`
- `docs/specs/01_init-cicd_291026/05_host-verification/spec.md`
- Spec 07 certificate and spec 13 backup status contracts
- OBS-01 to OBS-08; HV-06 to HV-08; DEP-18

## Proposed approach

1. Add the monitoring verification task to the existing role and `playbooks/verify.yml`. Verify collector activity, remote ingestion, required sources, and current disk/inode use at the 85% threshold; the alert rule retains its separate 15-minute persistence window. Keep verification read-only and preserve the stable PASS/FAIL output.
2. Document dashboard use, alert response, missing-data behavior, collector/token recovery, external-probe operation, backup/certificate signals, quota review, and central-log diagnosis of a failed rollout.
3. Run a Staging end-to-end acceptance covering every OBS-02 signal, every OBS-03 alert, the external route probe, collector loss, secret-redaction canaries, and centrally diagnosed failed rollout.
4. Confirm the approved primary and escalation recipients receive the rehearsed alerts. If Q5 approval is absent, leave alert delivery and this task blocked; do not substitute a test address.
5. Verify the plan/usage estimate and first-full-month comparison. Keep Production host-down and backup-age alerts as explicit go-live gates.
6. Record sanitized commands, run URLs, commit IDs, host aliases, dates, and results in this task's summary. Never record endpoint/tenant values, recipient addresses, secrets, or sensitive host details.

## Acceptance criteria

- `verify-vps.yml` remains the only host-verification workflow and checks monitoring without remediation or credential output.
- A collector/telemetry failure or current disk/inode use at or above 85% fails the monitoring verification check.
- All OBS-02 signals and required alerts are demonstrated on Staging; missing or stale data does not pass.
- The external probe detects a controlled route failure independently of Alloy, and stopping Alloy triggers the heartbeat alert.
- A failed rollout can be diagnosed from central logs without VPS login, and canary secrets/request-only fields are absent from all telemetry.
- Alert delivery and quota acceptance are supported by an approved route and dated evidence; otherwise the relevant checklist items remain unchecked.
- The runbook gives safe operator actions and contains no credentials, endpoint/tenant values, recipient addresses, or sensitive host details.

## Source reference

OBS-01 to OBS-08; HV-06 to HV-08; DEP-18; v5 §§13.1, 15.6, 16 step 11.

## Verify

- Run the repository's workflow/name checks, Ansible syntax/lint, and focused role/log/alert tests.
- Run `verify-vps.yml` against Staging and inspect sanitized PASS/FAIL output.
- Rehearse all required alerts and the external probe in Staging; review only sanitized results.
- Search logs, dashboard labels/queries, run summaries, and task evidence for canary values and forbidden request fields.
- Review the runbook against specs 05, 07, and 13 and confirm the Production gates are not weakened.

## Out of scope

Production fault injection, alert destination selection without approval, host remediation from verification, and the separate OBS-09 per-app dashboards.
