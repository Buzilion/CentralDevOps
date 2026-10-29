# Task 4: Grafana dashboards

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/14_observability-and-alerting/spec.md` |
| Depends on | Tasks 2 and 3 |
| Needs | Staging telemetry for every currently configured signal |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Provide reviewed, repeatable dashboards for platform health and per-app troubleshooting using the shared telemetry contracts.

## Relevant files or references

- `monitoring/grafana/dashboards/`
- `monitoring/grafana/`
- `docs/runbooks/observability-and-alerting.md`
- OBS-02, OBS-07, OBS-09

## Proposed approach

1. Create a platform overview dashboard grouped by Environment and host for CPU, RAM, disk/inodes, container restarts/health, Nginx errors, certificate expiry, PostgreSQL availability/connections, backup age, and telemetry/quota status.
2. Create one reusable app-health dashboard with Environment and app selectors for HTTP availability, latency, 5xx rate, relevant container health, and sanitized logs.
3. Use only bounded labels and reviewed queries. Missing or stale data must be visible and must not render as zero/healthy.
4. Store dashboard definitions in the repository and apply them to Grafana Cloud through the approved operator workflow. Do not put an administrative credential on a VPS or reuse the ingestion token for administration.
5. Validate panel queries against synthetic Staging data and keep exported definitions synchronized with the deployed dashboards.

## Acceptance criteria

- Every OBS-02 signal is visible and queryable for each Environment and applicable host/app.
- The app dashboard is shared and filtered by app; it does not create per-app dashboard forks.
- Dashboards clearly distinguish no-data/stale states from zero values and healthy states.
- Dashboard definitions contain no endpoints, tenant IDs, recipient addresses, credentials, or unbounded labels.
- A sanitized task summary identifies the deployed dashboard definitions and verification evidence.

## Source reference

OBS-02, OBS-07; OBS-09 is Could and excluded as a per-app dashboard requirement; v5 §13.1.

## Verify

- Validate dashboard JSON and every referenced metric/log query.
- Test Environment/app selectors with Staging fixtures and confirm each signal returns the expected series.
- Remove a test series and verify its panel reports no data instead of a healthy zero.
- Compare deployed dashboard exports with the checked-in definitions.

## Out of scope

Individually maintained dashboards per app, alert delivery, external probe setup, and plan selection.
