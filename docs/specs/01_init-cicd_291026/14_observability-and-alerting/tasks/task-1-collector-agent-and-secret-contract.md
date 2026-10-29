# Task 1: Collector agent and secret contract

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Spec-level gate: specs 05 and 13 complete; no preceding task |
| Needs | Reviewed spec 04 configure profiles, spec 05 verifier contract, and approved Staging Grafana Cloud connection details |
| Summary | Write `summaries/task-1-summary.md` when this task closes |

## Goal

Establish one pinned, hardened Alloy collector configuration per VPS and a clear Environment-scoped credential/endpoint contract without exposing provider values.

## Relevant files or references

- `roles/monitoring_agent/`
- `playbooks/configure.yml`
- `playbooks/verify.yml`
- `docs/design/variables-and-secrets.md`
- `docs/design/naming-and-repository-conventions.md`
- Spec 04 configure profile contract and spec 05 role-check contract
- `docs/prd/01_init-cicd_291026/observability-v1.md` (OBS-01, OBS-05)

## Proposed approach

1. Reconcile the `monitoring_agent`/`collector` wording in spec 04 and the naming convention. Use `roles/monitoring_agent` as the one canonical Ansible role, and ensure the configure profiles that can target a VPS include its required collector configuration.
2. Record separate Environment variables for metrics/logs endpoints and tenant identifiers where the selected Grafana stack requires them. Use the existing `MONITORING_GRAFANA_CLOUD_TOKEN` Environment secret, unique per Environment and scoped only for the required metrics/log writes. Update the variable catalog without copying any actual endpoint, identifier, or token value.
3. Pin the reviewed Alloy release and verify its checksum. Install a hardened systemd service with root-owned configuration, restrictive credential-file permissions, and only the local source access it needs.
4. Send telemetry only to the selected Environment's approved Grafana endpoints over TLS. Do not configure alert contact points in this task.
5. Add focused tests for missing/wrong Environment inputs, secret-file ownership/mode, no token in process arguments or logs, service hardening, check-mode safety, and idempotence.

## Acceptance criteria

- One canonical `monitoring_agent` role configures Alloy on every intended VPS profile; no duplicate collector role/service is added.
- Collector version and checksum are pinned and reviewed.
- Staging and Production use independent endpoints/tenant identifiers and distinct credentials; no Environment fallback is possible.
- The token is not committed, displayed, passed as a process argument, or readable by `cdo-deploy`.
- Alloy/exporter listeners are not public, and the role does not grant Docker access to app or deploy identities.
- Configure check mode is non-mutating and a second unchanged configure run reports no changes.
- The variable/secret catalog describes the final signal-specific names and handling without real values.

## Source reference

OBS-01, OBS-05; SEC-06, SEC-12; INF-03, INF-04; v5 §§6.2, 13.1; `variables-and-secrets.md` §§3.2, 4.8, 7.

## Verify

- Run focused Ansible syntax/lint and role tests for pinned install, file permissions, check mode, and idempotence.
- Inspect effective service configuration and process arguments without printing the secret.
- Verify Staging remote-write success and use synthetic credentials to prove the other Environment's endpoint/identity is rejected.
- Inspect firewall/listeners and group memberships; confirm no public exporter or deploy-user Docker access.

## Out of scope

Dashboard/alert creation, alert routing, external uptime probes, database/certificate/backup exporters, and Production fault injection.
