# 08 — End-to-end verification and troubleshooting

## Learning objectives

You can verify the complete public request path without disabling client security checks, classify common failures by layer, test an upstream outage safely, and preserve useful sanitized evidence.

## Prove each boundary

Run checks from both the VPS and an independent external network. These tests prove different things:

| Check | What it establishes | What it does not establish |
|---|---|---|
| DNS query | Resolver's current name/address answer | Reachability or correct app |
| Local upstream request | App responds on the proxy-to-app path tested | Public DNS, firewall, TLS |
| TCP probe to 443 | A connection can be established | Valid certificate or correct route |
| `curl https://hostname/` without `-k` | Normal TLS validation and an HTTP response | Correct authorization or every application route |
| External port test | Observed reachability from that network/address family | Reachability from all client networks |
| Proxy config test | Configuration parses according to the installed binary | Live behavior, certificate correctness, app health |

Do not use `curl -k`/`--insecure` as success evidence; it disables certificate verification and can hide the problem being investigated. If inspecting a known diagnostic, state explicitly that certificate validation was bypassed and do not treat it as acceptance.

## A compact test set

Replace placeholders with values that you control:

```sh
dig +noall +answer app.example.com A
dig +noall +answer app.example.com AAAA
curl -sS -D - -o /dev/null http://app.example.com/
curl -sS -D - -o /dev/null https://app.example.com/
curl -sS -D - -o /dev/null https://app.example.com/known-health-path
openssl s_client -connect app.example.com:443 -servername app.example.com -verify_return_error </dev/null
```

Use a PowerShell equivalent or another HTTP/TLS client where these utilities are unavailable. Do not publish verbose output containing addresses, headers, internal names, or certificate details beyond what the evidence audience needs. Test API and static routes separately. Test IPv6 only if it is published/configured. Test expected-closed upstream and database ports from outside the VPS.

Check HTTP behavior: correct hostname, HTTPS redirect with path/query preserved, expected status/content type, expected cache headers, no redirect loop, and a valid health/readiness result. A health endpoint should not disclose secrets or sensitive internals. Test app authentication separately; a `200` on the home page alone is not proof of application correctness.

## Diagnose by response

- **DNS points elsewhere or no answer:** inspect authoritative records, delegation, TTL, and address-family configuration.
- **TCP timeout/refusal:** check route, provider/host firewall, listener, and IPv4 versus IPv6 separately.
- **TLS name/chain/date error:** check SNI, hostname SAN, served chain, certificate dates, system clock, and renewal.
- **301/308 loop:** compare the proxy's external scheme header and the app's trusted-proxy/HTTPS settings.
- **404 or wrong content:** inspect virtual host, path rewrite/trailing slash, API/static routing, and app base path.
- **502:** inspect proxy-to-upstream resolution, port, network membership, listener, and app health.
- **504:** inspect upstream response time, application workload, and the relevant bounded timeout; do not simply increase all timeouts.

Observe proxy logs and application logs at the same time as a request. Correlation is stronger when a generated request ID is recorded by both, but redact sensitive values before retaining evidence.

## Controlled failure test

In a safe window or staging target, make the upstream unavailable using the service's normal stop/restart operation, then request the site. Verify the proxy returns an honest failure (not a stale or success-shaped response), logs a useful cause, and recovers after the app returns. Do not delete data or certificates to simulate a failure. Record how quickly recovery occurred and which operator action was needed.

## Evidence and maintenance

Retain a brief test record with date/time and timezone, client network type, tested hostname (use a sanitized alias if needed), address family, expected result, observed status, and disposition. Avoid raw headers, tokens, full client IPs, private keys, and sensitive application data. Repeat core checks after DNS, firewall, proxy, certificate, or deployment changes.

## Knowledge check

1. Why is a successful TCP connection to port 443 not proof of a valid HTTPS endpoint?
2. What failure classes can a local `curl` to the app not rule out?
3. What should a controlled upstream failure return and log?
4. Why is an insecure TLS client option invalid as a production acceptance test?

## Practical checkpoint

Complete [Task 06 — Test public behavior, isolation, and failure cases](../tasks/06-test-public-behavior-isolation-and-failure-cases.md), then finish the runbook in Task 07.

## References

- [curl: TLS certificate verification](https://curl.se/docs/sslcerts.html)
- [OpenSSL: s_client](https://docs.openssl.org/3.0/man1/openssl-s_client/)
- [NGINX: Troubleshooting](https://docs.nginx.com/nginx/admin-guide/monitoring/logging/)
