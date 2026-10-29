# Task 4: Atomic route activation

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md` |
| Depends on | Tasks 1–3 |
| Needs | Disposable host and a test domain; all issuance tests use the CA staging endpoint |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Replace the spec 04 fail-closed route stub with a constrained, idempotent route manager that safely activates HTTP-01 and HTTPS routes.

## Relevant files or references

- Update `deployment/scripts/centraldevops-route`
- Install it at `/usr/local/sbin/centraldevops-route` with its existing owner, mode and sudo boundary
- Use the templates from Task 2 and DNS check from Task 3
- Spec sections: Route activation and rollback, TLS policy, Deployment integration and Q8 decision
- RTE-01 to RTE-06, RTE-09, RTE-10

## Proposed approach

1. Implement only the documented `apply` and `confirm` operations. Validate each argument, derive filenames and aliases internally, and reject unsupported modes before file access.
2. Require the central caller to have already validated the domain against the registry; repeat canonical hostname and syntax checks on the host. Never accept a raw config file, arbitrary path or Nginx fragment.
3. For a new domain, repeat the DNS precondition, install and validate the HTTP-only challenge route, reload Nginx, request a webroot certificate, then validate and reload the HTTPS route.
4. For an existing route, avoid a certificate request when the current certificate is valid. For a changed domain, keep the prior route active until the new HTTPS candidate validates.
5. Serialize route edits/reloads using the shared proxy lock. Write candidates atomically; on config-test failure restore the previous file and do not reload the invalid candidate. Surface reload and rollback errors explicitly.
6. Skip file writes, Certbot calls and reloads when route content is unchanged.
7. Invalidate HSTS confirmation when the route fingerprint changes. `confirm` may enable HSTS only for the current Production route after spec 11 reports a successful external HTTPS smoke test; it must not enable HSTS in Staging.

## Acceptance criteria

- Invalid arguments, DNS mismatch and unsupported mode fail without changing active route files or requesting a certificate; the central caller rejects unlisted domains before invoking the route command.
- A new route transitions through HTTP-01 to HTTPS; app traffic is never proxied over plain HTTP.
- An invalid Nginx candidate restores the last known-good file, does not reload that candidate and leaves another app route serving.
- A reload failure is surfaced and restores/validates the prior configuration.
- An unchanged route causes no rewrite, Certbot request or reload.
- Domain changes preserve the prior route until the new HTTPS route is ready.
- HSTS confirmation is root-owned, tied to the active route fingerprint, idempotent and Production-only.
- IPv4 and IPv6 listeners are consistent with the proxy inventory and DNS answer set.

## Source reference

RTE-01 to RTE-06, RTE-09, RTE-10; INF-12; DEP-10 to DEP-12; v5 §§8.3–8.5, 10.2–10.4.

## Verify

- Run script tests with mocked `nginx`, `certbot`, resolver and reload commands.
- Assert restore behavior, no-reload behavior, unchanged route behavior, independent app routes and command exit codes.
- On the disposable host, issue only a staging certificate and verify the rendered HTTPS route externally.

## Out of scope

The central deployment workflow, runner-side smoke-test reporting, automatic rollback after smoke failure, or implementation of `private_ip`.
