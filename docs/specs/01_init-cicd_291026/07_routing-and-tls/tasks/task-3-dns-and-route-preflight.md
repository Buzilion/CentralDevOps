# Task 3: DNS and route preflight

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/07_routing-and-tls/spec.md` |
| Depends on | Task 1; spec 06 registry/manifest schemas and placement contract complete |
| Needs | DNS resolver tests use mocked responses; no certificate credentials |
| Summary | Write `summaries/task-3-summary.md` when this task closes |

## Goal

Reject stale or incorrect DNS and unsupported placement before a deployment connects to a host or requests a certificate.

## Relevant files or references

- Create `deployment/tools/check-domain-dns.py` and focused tests
- Extend `deployment/scripts/centraldevops-compose-policy` with a route-specific alias check and tests
- Use `proxy_public_ips` from the selected proxy host in the selected Environment inventory
- Reuse the registry/manifest validation contract from spec 06; do not duplicate its schema
- Spec sections: Placement and configuration ownership, DNS precondition
- RTE-02, RTE-03; REG-01 to REG-04

## Proposed approach

1. Add a standard-library DNS check that resolves the domain's terminal A/AAAA addresses and compares the complete result set with the inventory's `proxy_public_ips`.
2. Require a non-empty list of valid public IP literals. An absent/invalid list, empty DNS response, resolver error, missing expected address or unexpected address fails closed.
3. Run this check on the central runner before SSH for every route activation. Install the same checker at `/usr/local/lib/centraldevops/check-domain-dns.py` so `centraldevops-route` repeats it immediately before a new Certbot request using `/etc/centraldevops/proxy-public-ips.json`.
4. Use the selected registry and manifest outputs: reject a domain outside the app/Environment allow-list, `routing.tls: false`, and `private_ip` before DNS/SSH. Do not accept an expected IP, `EDGE_ALIAS` or placement mode from workflow input or app data.
5. Derive the edge alias as `<app-slug>-<environment-path>` and ensure the rendered Compose route service advertises that alias on external `edge`; the app manifest cannot set or override it.
6. Add negative tests proving failures return a clear domain/address diagnostic and cannot invoke SSH or Certbot.

## Acceptance criteria

- Exact matching IPv4 and IPv6 answer sets pass; missing, stale, extra or malformed addresses fail.
- DNS failure prevents SSH and makes no certificate request.
- An unlisted domain or unsupported `private_ip` route fails before connection.
- An IPv6 DNS answer without a matching configured public IPv6 address fails; a configured IPv6 address requires a working IPv6 HTTP/HTTPS listener and firewall path.
- The rendered Compose route service is rejected if its `edge` alias is missing or differs from the central derived alias.
- Expected addresses come only from the selected proxy inventory and the root-owned host configuration.
- No DNS provider API, wildcard route or app-controlled upstream is introduced.

## Source reference

RTE-02, RTE-03; REG-01 to REG-04; INF-07, INF-08; v5 §§9.1–9.2, 10.1–10.2.

## Verify

- Run focused tests for matching A/AAAA data, stale and extra records, missing records, invalid inventory values and resolver failures.
- Use an invocation spy to prove failed preflight does not call SSH or Certbot.
- Review the workflow call site to confirm preflight runs before any host connection.

## Out of scope

Managing DNS records, resolving the open RTE-13 split-host capability, or issuing a certificate.
