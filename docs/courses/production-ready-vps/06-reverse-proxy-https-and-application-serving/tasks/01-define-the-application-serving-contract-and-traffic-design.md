# Task 01 — Define the application-serving contract and traffic design

## Outcome

Produce a verified request/serving contract and one-page traffic design for the actual application. The proxy design will be based on observed repository/runtime facts, not framework assumptions.

## Prerequisites

- Read [Lesson 01 — The request path, reverse proxies, and trust boundaries](../lessons/01-the-request-path-reverse-proxies-and-trust-boundaries.md).
- Have read access to the application repository and the release/runtime contract from the earlier Docker and CI/CD subjects.
- Do not copy production secrets, private keys, customer data, or public infrastructure identifiers into the deliverable.

## Procedure

1. Inspect the application's README/deployment documentation, Dockerfile/Compose configuration, environment-variable examples, build/start commands, and relevant application configuration. Record the commit or release identifier inspected.
2. Record the actual internal listening port and bind address, startup/readiness behavior, expected base URL/host, health path (if one exists), and whether the service itself expects TLS.
3. Identify which component serves page HTML, static files, API routes, uploads, and WebSockets. Mark each as **verified**, **not applicable**, or **unknown**; resolve unknowns before proxy configuration rather than guessing.
4. For each route family, record its public path, upstream path transformation (if any), expected status/content type, authentication behavior, and any required body-size or timeout behavior.
5. Draw a request-flow diagram showing DNS, provider/host firewall, proxy, private upstream, TLS termination point, and trusted-proxy metadata boundary. Show IPv4 and IPv6 separately if both are used.
6. Decide whether the proxy runs on the host or as a container, and record the exact upstream addressing model. State why the application port will not be public.
7. Define the intended hostname(s), HTTP behavior, HTTPS requirement, and policy for unknown hostnames.
8. List unresolved assumptions and block public rollout for any unresolved item that could expose the wrong service or break authentication/HTTPS behavior.

## Acceptance criteria

- [ ] Evidence identifies the inspected application revision and actual runtime listen port/address.
- [ ] Static, API, upload, health, and WebSocket behaviors are individually marked verified, not applicable, or unresolved.
- [ ] Public and upstream paths are explicit; no path stripping or SPA fallback is assumed without evidence.
- [ ] Diagram labels public listeners, private upstream, TLS termination, address families, and trust boundary.
- [ ] The selected proxy placement is compatible with the actual host/container network path.
- [ ] Unknown hostname behavior and the HTTP-to-HTTPS policy are stated.
- [ ] No credentials, customer data, private keys, or unnecessary public IP details are included.

## Deliverable

A sanitized serving-contract table and traffic diagram committed alongside the course's deployment documentation or stored in the team's approved operational record.
