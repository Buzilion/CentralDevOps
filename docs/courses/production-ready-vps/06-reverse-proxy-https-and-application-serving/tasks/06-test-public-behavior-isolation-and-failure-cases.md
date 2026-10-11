# Task 06 — Test public behavior, isolation, and failure cases

## Outcome

Prove from an external client that the real hostname serves the intended app over valid HTTPS, only intended ports are exposed, and an upstream failure is visible and recoverable.

## Prerequisites

- Complete Tasks 01–05.
- Read [Lesson 08 — End-to-end verification and troubleshooting](../lessons/08-end-to-end-verification-and-troubleshooting.md).
- Have a safe maintenance window or non-production target for the controlled failure test.

## Procedure

1. From a separate network, resolve A and AAAA independently. Test each published address family; do not count a server-local request as an external test.
2. Verify HTTP redirect and HTTPS using a standard client with certificate verification enabled. Record the hostname, status, location, and result without retaining unnecessary headers or addresses.
3. Exercise the actual homepage, health/readiness path, one valid API path, expected API error, representative static asset, and upload/WebSocket path if applicable. Check status, content type, redirect behavior, and cache policy.
4. Test intended closed ports (application, database, admin interfaces) externally for each published address family. Compare results with provider firewall, host listener, and Docker exposure configuration.
5. In a safe window, stop or isolate the upstream using its normal service operation. Confirm the public site returns an honest failure, the proxy logs identify the upstream problem, and it recovers after the app restarts. Do not delete state or certificates.
6. Check proxy and application service state/logs during the test. Investigate every unexpected result by layer instead of disabling TLS checks or opening additional ports.
7. Store sanitized evidence with timestamp/timezone, client network type, address family, expected result, observed result, and resolution.

## Acceptance criteria

- [ ] DNS, TCP reachability, TLS validation, HTTP routing, and application health are recorded as separate results.
- [ ] No insecure TLS verification bypass is used to claim HTTPS success.
- [ ] IPv4 and IPv6 results are represented independently when applicable.
- [ ] The origin app and database ports are externally unreachable.
- [ ] Required page/API/static/realtime paths behave as specified; inapplicable routes are marked.
- [ ] Controlled upstream failure produces a diagnosable non-success response and recovery is demonstrated.
- [ ] Evidence is sanitized and sufficient for another operator to reproduce.

## Deliverable

A dated external verification matrix and controlled-failure record.
