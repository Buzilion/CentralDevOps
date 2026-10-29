# Task 6: Disposable-host acceptance and runbook

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md` |
| Depends on | Tasks 1–5; specs 04, 05 and 06 checklists complete |
| Needs | Disposable Ubuntu host and controlled test domain; staging CA only |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Prove routing, TLS, renewal and verification behavior safely on a disposable host, then document the operator workflow and retain sanitized evidence.

## Relevant files or references

- Create `docs/runbooks/routing-and-tls.md`
- Create a sanitized `summaries/task-6-summary.md` when accepted
- Spec requirements RTE-01 to RTE-06 and RTE-08 to RTE-10
- INF-06, INF-18; the alert handoff to spec 14

## Proposed approach

1. Confirm the disposable host is independent of Staging and Production service hosts and has verified inventory public addresses. Configure DNS for a controlled test domain.
2. Exercise DNS success and failure paths; verify bad/missing records fail before SSH and no certificate request is made.
3. Activate a new route using the CA staging endpoint. Verify the HTTP-01 challenge, HTTPS response, redirect, forwarded headers, timeouts and supported TLS versions.
4. Reapply the same route and prove zero file rewrites, Certbot requests and Nginx reloads. Inject an invalid candidate and a reload failure; verify rollback and another app route's availability.
5. Verify HSTS is absent for new routes and Staging, and appears only after a successful Production-mode fixture is confirmed; do not use a Production host or certificate for this test.
6. Run a Certbot renewal dry run against the staging endpoint and prove the hook does not reload after a failed `nginx -t`.
7. Exercise verification with synthetic certificates around the 21-day threshold and inspect the alertable metric output.
8. Document manual DNS setup, safe route activation, renewal/expiry checks, failure handling and recovery. Record sanitized commands/results and leave all checklist tasks unchecked if required evidence is missing.

## Acceptance criteria

- All required route, DNS, idempotence, rollback, TLS, HSTS, renewal and expiry checks pass on the disposable host or in focused tests.
- No Production host, Production credential or production certificate is used.
- Every certificate-issuance test uses the CA staging endpoint.
- The runbook explains the no-auto-rollback Q8 decision and the spec 14 alert handoff.
- Evidence records the test date, disposable host alias, test domain, commit/run references and outcomes; it contains no credentials or private host data.

## Source reference

RTE-01 to RTE-06, RTE-08 to RTE-10; INF-06, INF-16, INF-18; v5 §§10.2–10.4, 13.1, 15.1, 16 step 6.

## Verify

- Review sanitized evidence against each invariant in `spec.md`.
- Run workflow lint, name checks, focused tests and Ansible syntax/lint checks.
- Re-run route activation unchanged and confirm zero rewrites/reloads; confirm all expiry and failure cases report the expected result.

## Out of scope

Applying the roles to a Production service host, using a production ACME certificate for tests, deploying a real app, or enabling `private_ip`.
