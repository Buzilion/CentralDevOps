# Reverse Proxy, HTTPS, and Application Serving — Course Checklist

Complete this subject after **Linux Server Administration**, **Networking, DNS, and Firewall Security**, **Docker and Container Operations**, **Infrastructure Automation with Ansible**, and **CI/CD with GitHub Actions**. The application release and runtime contract must be known; the VPS must have a secure baseline and a recoverable deployment. This subject publishes the application through a controlled web entry point. It does not configure backups, full monitoring, or CI/CD.

Use a real domain only when you control it and can change its DNS. Replace every example hostname, address, port, and path with values verified from the application and VPS. Do not publish credentials, private keys, certificate private material, or identifying infrastructure details in course evidence.

## Lessons

- [ ] [01 — The request path, reverse proxies, and trust boundaries](lessons/01-the-request-path-reverse-proxies-and-trust-boundaries.md)
- [ ] [02 — Domain, DNS, firewall, and listener preflight](lessons/02-domain-dns-firewall-and-listener-preflight.md)
- [ ] [03 — Choosing and configuring Nginx or Caddy](lessons/03-choosing-and-configuring-nginx-or-caddy.md)
- [ ] [04 — HTTP routing, forwarded headers, limits, and timeouts](lessons/04-http-routing-forwarded-headers-limits-and-timeouts.md)
- [ ] [05 — TLS certificates, HTTPS, and renewal](lessons/05-tls-certificates-https-and-renewal.md)
- [ ] [06 — Serving static assets, APIs, and WebSockets](lessons/06-serving-static-assets-apis-and-websockets.md)
- [ ] [07 — Safe proxy changes, logs, and operational controls](lessons/07-safe-proxy-changes-logs-and-operational-controls.md)
- [ ] [08 — End-to-end verification and troubleshooting](lessons/08-end-to-end-verification-and-troubleshooting.md)

## Hands-on tasks

- [ ] [Task 01 — Define the application-serving contract and traffic design](tasks/01-define-the-application-serving-contract-and-traffic-design.md)
- [ ] [Task 02 — Prove DNS, firewall, and origin preconditions](tasks/02-prove-dns-firewall-and-origin-preconditions.md)
- [ ] [Task 03 — Configure a minimal reverse proxy and prove private upstream access](tasks/03-configure-a-minimal-reverse-proxy-and-prove-private-upstream-access.md)
- [ ] [Task 04 — Issue and verify a production TLS certificate](tasks/04-issue-and-verify-a-production-tls-certificate.md)
- [ ] [Task 05 — Configure application routes, headers, and bounded request behavior](tasks/05-configure-application-routes-headers-and-bounded-request-behavior.md)
- [ ] [Task 06 — Test public behavior, isolation, and failure cases](tasks/06-test-public-behavior-isolation-and-failure-cases.md)
- [ ] [Task 07 — Document proxy operations, renewal, and recovery](tasks/07-document-proxy-operations-renewal-and-recovery.md)

## Subject completion gate

- [ ] The serving contract is based on inspected application configuration, not guessed ports, paths, static-file behavior, or WebSocket requirements.
- [ ] The domain resolves to the intended VPS; every published address family has been tested end to end.
- [ ] The proxy is the only public web entry point. The application listener is private and unreachable directly from the public internet.
- [ ] HTTP redirects to HTTPS without creating a redirect loop; the certificate is valid for the requested hostname and renews through a tested mechanism.
- [ ] Proxy forwarding headers are deliberate, and the application trusts proxy metadata only from the proxy boundary.
- [ ] API, static, upload, and WebSocket behavior (when applicable) has been tested without weakening unrelated routes.
- [ ] Request sizes and timeouts are bounded to the application's real needs; security headers are compatible with the application.
- [ ] Configuration validation, reload, logs, renewal status, and rollback/recovery procedures are documented and rehearsed.
- [ ] Tests cover external IPv4/IPv6 where applicable, certificate validation, expected closed ports, application health, and a controlled upstream failure.

## Exit criteria

The application is reachable at its intended domain over valid HTTPS, the proxy routes requests to the intended private upstream, and no unnecessary origin port is publicly exposed. An operator can validate and safely reload the proxy, diagnose a failed request, and confirm how certificate renewal and configuration recovery work. Proceed to **Data Persistence, Backup, and Recovery** only after this serving boundary is understood and its operational evidence is recorded.
