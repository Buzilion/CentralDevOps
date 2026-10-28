# Task 05 — Configure application routes, headers, and bounded request behavior

## Outcome

Configure only the routes and proxy behaviors required by the actual application, then demonstrate that normal, invalid, oversized, cached, and real-time requests behave as intended.

## Prerequisites

- Complete Tasks 01–04.
- Read [Lesson 04 — HTTP routing, forwarded headers, limits, and timeouts](../lessons/04-http-routing-forwarded-headers-limits-and-timeouts.md) and [Lesson 06 — Serving static assets, APIs, and WebSockets](../lessons/06-serving-static-assets-apis-and-websockets.md).

## Procedure

1. Implement the Task 01 route table. Preserve application paths unless an explicit transformation was verified. Keep API failures distinct from a frontend SPA fallback.
2. If proxy-served static files are used, set caching according to content identity: long-lived immutable caching only for fingerprinted assets; revalidation/no-cache behavior for mutable HTML or manifests. Verify missing assets return 404.
3. Set request-body limits from real upload/API needs. Set upstream connect/read/send timeouts based on request behavior. Document why each non-default value exists; do not make every timeout unlimited.
4. Configure the required host, scheme, and client forwarding behavior. Confirm the app trusts only the proxy's private source and generates HTTPS links/cookies correctly.
5. Add security headers only when compatible with the application and avoid duplicate/conflicting values. Test CSP changes in browser tooling if one is set. Add HSTS only under the reviewed policy from Task 04.
6. If WebSockets are actually used, configure the documented path and upgrade behavior. Verify handshake, authentication, origin handling, idle/heartbeat, and reconnect behavior. If not used, record not applicable and do not add broad upgrade rules.
7. Validate the proxy config and reload. Exercise representative pages, a valid API call, an API 404, a missing asset, a maximum-size boundary (where applicable), and WebSocket behavior (where applicable).

## Acceptance criteria

- [ ] Each configured path has a documented intended handler and upstream path.
- [ ] An API error is not converted into successful HTML by a generic fallback.
- [ ] Static cache policy differentiates immutable fingerprinted assets from mutable entry documents.
- [ ] Body sizes and timeouts are finite, justified, and compatible with required app behavior.
- [ ] Application-generated URLs and secure-cookie behavior reflect external HTTPS through a narrowly trusted proxy.
- [ ] WebSocket support is either verified end to end or explicitly not applicable.
- [ ] Any new security header has a reviewed value and does not break the required app behavior.

## Deliverable

An updated route/configuration table and sanitized test results for normal and boundary requests.
