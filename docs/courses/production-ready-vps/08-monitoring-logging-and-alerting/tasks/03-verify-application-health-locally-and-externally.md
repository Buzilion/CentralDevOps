# Task 03 — Verify application health locally and externally

## Outcome

Demonstrate the difference between a local process/application check and a public user-path check, and verify the real DNS-to-HTTPS-to-application path without disclosing private dependency details.

## Prerequisites

- Read [Lesson 03 — Application health, readiness, and external uptime checks](../lessons/03-application-health-readiness-and-external-uptime-checks.md).
- Have the monitoring contract from Task 01 and a deployed application with an approved public hostname.
- Do not change production health behavior without an application owner-approved release and rollback plan.

## Procedure

1. Inspect current health-check routes and container/process-manager settings. Write down what each check means and which component consumes its result. If no suitable endpoint exists, document the smallest application change required; do not invent a route or claim an existing homepage is readiness.
2. Define liveness, readiness, and user-facing synthetic checks separately where applicable. Specify response, timeout, retry/failure window, polling cadence, side effects, authentication, and safe output for each.
3. From the VPS or an approved private runner, verify the local/proxy-to-app path and capture sanitized status, duration, and time. Check the expected healthy result and a controlled non-production dependency/unavailable response if safely possible.
4. Configure an external probe that runs outside the VPS and checks the intended public hostname over HTTPS. Validate expected status/content without credentials or dynamic customer content. Verify certificate name and validity, redirect, and response duration.
5. Test every published address family (IPv4 and IPv6 where configured). Confirm the provider firewall, host firewall, reverse proxy, and private upstream behavior align with the earlier exposure design.
6. Confirm a known safe failure is detected with the expected timing using a test/staging endpoint or the monitoring service's test facility. Do not take down the production application for this step.
7. Verify probe data freshness, location, provider outage behavior, notification ownership, and access controls. Record the independent route for checking service status if the probe provider is unavailable.

## Acceptance criteria

- [ ] Health check semantics and consuming component are documented; liveness is not confused with readiness.
- [ ] Checks are bounded, side-effect-free, and do not disclose stack traces, internal hosts, versions, secrets, or dependency internals publicly.
- [ ] The local check and external public check produce distinct evidence for their intended layers.
- [ ] The external check validates the configured hostname, HTTPS certificate, expected safe response, and acceptable latency.
- [ ] Every published address family has been tested; unconfigured families are explicitly noted.
- [ ] The application/upstream remains private except through the intended public proxy.
- [ ] Probe failure and recovery behavior has been safely exercised or verified with a provider test function.
- [ ] Evidence contains no credentials, personal data, raw response body, or unnecessary private infrastructure values.

## Deliverable

A dated **health and external-check validation record** with check definitions, path covered, result and latency, failure/recovery evidence, tested address families, and any application work still required.
