# Task 7: Ingestion estimate and quota review

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Tasks 1, 2, 3, and 5 |
| Needs | Current inventories/registry, Staging telemetry, approved Grafana plan quota details |
| Summary | Write `summaries/task-7-summary.md` when this task closes |

## Goal

Show that the selected Grafana Cloud plan can carry the required signals before Production and measure actual use against the forecast.

## Relevant files or references

- Create `docs/observability/ingestion-estimate.md`
- `monitoring/grafana/dashboards/`
- `docs/design/variables-and-secrets.md`
- OBS-05, OBS-06; parent PRD Q10; v5 §§13.1, 17 #10

## Proposed approach

1. Estimate expected metric series/scrape volume, log ingestion by source, app/host counts, external probe schedule, alert evaluation, and retention using the current inventories and registry.
2. Compare the estimate with the selected plan's actual quotas and required feature support. Use the free plan only if it covers all required signals, alert rules, probes, and retention; otherwise choose a suitable paid plan or reduce ingestion before Production.
3. Add a quota/usage view or a dated provider-portal review process that covers metrics, logs, probes, and rule limits without requiring a host credential.
4. Run Staging telemetry for a full month before the Production gate, compare actual use with the estimate, and record any plan upgrade or log-volume reduction.
5. Record assumptions and measurements without endpoint values, tenant identifiers, token contents, or recipient addresses.

## Acceptance criteria

- A dated pre-go-live estimate uses actual configured host/app counts and documented volume assumptions.
- The selected plan's quotas and feature availability cover the forecast; a successful test push alone is not accepted as proof.
- A repeatable usage review covers metrics, logs, probes, alerts, and retention.
- After one full month of Staging operation, actual usage is compared with the forecast and an upgrade/reduction decision is recorded.
- If any required feature or quota is insufficient, the Production gate remains blocked.

## Source reference

OBS-05, OBS-06; parent PRD Q10; v5 §§13.1, 17 #10.

## Verify

- Recompute the estimate from inventory, registry, scrape intervals, expected log volume, and probe schedule.
- Compare the documented plan limits with each required feature and usage dimension.
- Inspect the usage dashboard or dated portal-review evidence for both Environments.
- Review the first-full-month comparison and confirm any required plan/log-volume change is recorded.

## Out of scope

Provider billing changes, purchase approval, actual Production plan upgrades, and any unapproved data-retention expansion.
