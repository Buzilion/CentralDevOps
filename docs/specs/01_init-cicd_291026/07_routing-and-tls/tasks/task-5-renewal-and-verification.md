# Task 5: Renewal and certificate verification

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md` |
| Depends on | Tasks 1 and 4; spec 05 verification framework complete |
| Needs | Disposable certificate fixtures; no Production certificate |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Renew certificates automatically without reloading invalid Nginx configuration, and expose certificate expiry through read-only verification and a monitoring signal.

## Relevant files or references

- Create `deployment/scripts/centraldevops-certbot-deploy-hook`
- Create `deployment/tools/check-cert-expiry.py`
- Add `roles/nginx/tasks/verify.yml` and `roles/certbot/tasks/verify.yml`; update `roles/certbot/` and `playbooks/verify.yml`
- Metric path: `/var/lib/centraldevops/metrics/certificate-expiry.prom`
- Spec sections: TLS policy, verification and renewal; Error Behavior
- RTE-08; INF-06, INF-18; OBS-01, OBS-03

## Proposed approach

1. Configure the Certbot systemd timer to use a root-owned deploy hook that acquires the shared proxy lock, runs `nginx -t`, and reloads Nginx only after validation succeeds.
2. On validation failure, return nonzero and do not reload. Do not suppress Certbot or Nginx errors.
3. Add a read-only expiry checker that reports each managed domain and exact days remaining; expired certificates and certificates with fewer than 21 days remaining return FAIL.
4. Extend `verify-vps.yml` with Nginx service/configuration, Certbot timer and per-certificate expiry checks. Keep verification read-only and report one PASS/FAIL result per host/check.
5. Publish `centraldevops_certificate_expiry_days{domain="..."}` to the documented metrics file using an atomic, non-secret update. Refresh it daily with a systemd timer and after route/certificate changes.
6. Co-locate Nginx service/config checks and Certbot timer/certificate checks with their owning role; integrate both through the existing `playbooks/verify.yml` result contract.
7. Make a host with no expected routes/certificates report that none are configured rather than failing solely because the certificate directory is empty. The monitoring role and Grafana alert rule are delivered by spec 14.

## Acceptance criteria

- The renewal hook validates Nginx before every reload and shares the route mutation lock.
- A forced `nginx -t` failure prevents reload and is visible as a failed hook.
- Verification changes no host state and reports PASS/FAIL with domain and days remaining.
- `roles/nginx/tasks/verify.yml` and `roles/certbot/tasks/verify.yml` are invoked through the existing role-scoped verifier and produce one result per host/check.
- Expired and under-21-day certificates report FAIL; a certificate at or above the threshold passes.
- The daily metric refresh and route-change refresh atomically write a collector-readable file containing no secret material.
- The runbook/spec 14 handoff identifies the metric and threshold; alert delivery is not claimed complete until spec 14 integrates it.

## Source reference

RTE-08; INF-06, INF-18; OBS-01, OBS-03; v5 §§6.3, 10.3, 13.1.

## Verify

- Run expiry-checker tests with synthetic certificates below, at and above the 21-day boundary.
- Run renewal-hook tests with successful and failed Nginx configuration checks; assert reload counts.
- Run the repository's verification tests and confirm all certificate checks are read-only.

## Out of scope

Grafana dashboards/alert routing (spec 14), certificate-rate-limit recovery during disaster recovery (spec 13), or issuance using the production CA in tests.
