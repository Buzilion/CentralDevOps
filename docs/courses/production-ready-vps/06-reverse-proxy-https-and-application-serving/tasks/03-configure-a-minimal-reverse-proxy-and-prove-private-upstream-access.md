# Task 03 — Configure a minimal reverse proxy and prove private upstream access

## Outcome

Route the intended hostname to the verified application through one selected proxy while keeping the upstream private and retaining a recoverable configuration.

## Prerequisites

- Complete Tasks 01–02.
- Read [Lesson 03 — Choosing and configuring Nginx or Caddy](../lessons/03-choosing-and-configuring-nginx-or-caddy.md).
- Select Nginx or Caddy and decide whether it runs on the host or as a container.

## Procedure

1. Record the installed proxy version, service/container name, source-of-truth config path, and active listener. Remove or disable only conflicting default sites/configuration after preserving the known-good state.
2. Confirm the exact network path from proxy to app: loopback-bound published port for a host proxy, or private shared network/service name for a container proxy. Do not use a public app listener.
3. Add a minimal site for the intended hostname. Route to the verified upstream and preserve the host/path unless Task 01 documented a deliberate transformation. Reject or safely handle unknown hostnames.
4. If HTTPS is not ready, keep any public HTTP response limited to a non-sensitive setup response or the selected ACME challenge; do not expose authenticated application traffic over plain HTTP. Keep this temporary state bounded, and do not claim production readiness until Task 04's HTTPS checks pass.
5. Set only required forwarding headers. For a direct edge proxy, overwrite client-supplied forwarding metadata; if an upstream CDN/load balancer exists, trust only its verified ranges.
6. Save the previous config with owner and mode preserved. Run the proxy's native configuration validator, inspect the diff, reload using the supported mechanism, and verify service status and logs.
7. Test the route locally through the proxy using the intended Host header and externally by hostname. Confirm the expected response and verify no direct external connection to the upstream port succeeds.

## Acceptance criteria

- [ ] Exactly one selected proxy owns the intended public listener.
- [ ] Proxy upstream matches the inspected application contract and is reachable from the proxy's network namespace.
- [ ] The app is not bound/published on a public interface; external upstream-port tests fail.
- [ ] Unknown hostnames do not route to the application.
- [ ] The proxy validates before reload, and the active config can be restored.
- [ ] Proxy and app logs/status establish whether the test request reached the intended app.
- [ ] No broad trust of client-provided forwarding headers or TLS-verification bypass is configured.

## Deliverable

A reviewed minimal proxy configuration and sanitized before/after listener and route-test evidence.
