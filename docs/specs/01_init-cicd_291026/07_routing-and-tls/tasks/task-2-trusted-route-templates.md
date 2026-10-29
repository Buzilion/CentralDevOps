# Task 2: Trusted route templates

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md` |
| Depends on | Task 1 |
| Needs | No host credentials; use non-secret render fixtures |
| Summary | Write `summaries/task-2-summary.md` when this task closes |

## Goal

Create deterministic HTTP-only and HTTPS Nginx templates that accept validated route data but never app-authored proxy directives.

## Relevant files or references

- Create `deployment/nginx-templates/http-only.conf.j2`
- Create `deployment/nginx-templates/https.conf.j2`
- Add focused template-rendering tests under `deployment/tools/tests/`
- Spec sections: Placement and configuration ownership, Route activation and rollback, TLS policy
- RTE-01, RTE-04, RTE-09

## Proposed approach

1. Use the fixed route location `/opt/centraldevops/nginx/conf.d/<app>-<env>.conf`; derive the app/environment filename and `<app>-<env>` Docker edge alias in trusted code.
2. Make the HTTP-only template serve only `/.well-known/acme-challenge/` from the shared webroot and return no app content before certificate issuance.
3. Make the HTTPS template redirect other HTTP requests to HTTPS, permit TLS 1.2/1.3 only, and use the standard `Host`, `X-Real-IP`, `X-Forwarded-For` and `X-Forwarded-Proto` headers.
4. Render IPv4 and IPv6 listeners only for address families configured in the proxy inventory; do not make an AAAA route usable without its matching listener and firewall path.
5. Set explicit bounded connect/read/send timeouts. Do not expose arbitrary timeouts, locations, headers, include files or Nginx snippets to app input.
6. Keep HSTS disabled by default; render it only for a matching confirmed Production route. Use `max-age=86400`, without `includeSubDomains` or `preload`.
7. Escape or reject values before rendering; use only the validated domain, derived alias, numeric container port and trusted certificate paths.

## Acceptance criteria

- Both templates render deterministically and pass `nginx -t` with valid fixtures.
- Invalid hostnames, ports, aliases or template inputs are rejected rather than rendered.
- The HTTP challenge path remains available, while all other HTTP requests redirect after HTTPS activation.
- IPv4/IPv6 listeners match the configured address families; an unconfigured IPv6 address cannot be served accidentally.
- Legacy TLS versions are disabled; HSTS is absent by default and for Staging, and present only for confirmed Production rendering.
- No app-controlled value can introduce an Nginx directive or filesystem path.

## Source reference

RTE-01, RTE-04, RTE-09; REG-02; v5 §§9.1, 10.1–10.3.

## Verify

- Run template unit tests for valid and invalid fixtures.
- Run `nginx -t` against rendered HTTP-only and HTTPS configurations on the disposable test environment.
- Inspect rendered output for redirect, challenge, upstream, TLS, headers, timeouts and HSTS behavior.

## Out of scope

Installing Nginx, issuing certificates, DNS preflight, route activation or runner-side HTTPS smoke tests.
