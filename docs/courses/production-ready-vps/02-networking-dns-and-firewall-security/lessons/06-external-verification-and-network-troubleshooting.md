# 06 — External verification and network troubleshooting

## Learning objectives

You can prove the intended public attack surface from outside the VPS, distinguish common network failures, and retain useful, sanitized evidence of the final policy.

## Build an expected-exposure matrix

Before probing the host, write down what should be reachable now. Before application serving is configured, a fresh VPS might need only the administrative SSH endpoint; ports 80 and 443 can remain closed until the reverse proxy is intentionally deployed. Later, the public web edge may need TCP 80/443 while application and database ports remain private.

| Service | Protocol/port | Expected source | Public now? | Reason |
|---|---|---|---|---|
| SSH | Actual configured TCP port | Administrator or approved source range | Yes, if remote administration requires it | Managed access |
| HTTP | TCP 80 | Internet | Only when intentionally serving/redirecting web traffic | Web edge |
| HTTPS | TCP 443 | Internet | Only when TLS endpoint is ready | Web edge |
| Application | Actual application port | Local proxy/private network | No direct public exposure | Internal request handling |
| Database | Actual database port | Application/private network | No direct public exposure | Data service |

Adjust the matrix to the real services and operational requirements. Never mark an exposure “expected” merely because a scanner reports it.

## Test from a separate client

Run checks from a machine on a network independent of the VPS—for example, your workstation over a home or mobile connection. If your test client is behind the same provider network or VPN, note that limitation. Resolve DNS first, then test each expected port and protocol. From PowerShell, `Test-NetConnection HOST -Port PORT` checks TCP reachability. On a Unix-like client, `nc -vz -w 3 HOST PORT` is a common TCP check; tool options vary. A response from an open TCP connection says nothing by itself about application correctness or TLS.

Use `curl -v --connect-timeout 5 https://HOST/` only when HTTPS is actually configured. It tests DNS, TCP, TLS, and an HTTP exchange together, so inspect which stage failed. Do not turn off certificate verification to make a test appear successful; investigate the certificate name, chain, validity, and requested hostname.

Test IPv4 and IPv6 separately when both are published or enabled. `dig A`/`dig AAAA` checks DNS records; `curl -4` and `curl -6` can select address families when supported. A hostname that has an unreachable AAAA answer can fail for some users while IPv4-only tests pass.

## Interpret results carefully

- **Name lookup failure:** inspect records, delegation, resolver cache, and hostname spelling.
- **Timeout:** packets may be dropped, routed incorrectly, or filtered at the provider/host; also verify the destination address.
- **Connection refused:** the destination was reachable enough to reject the TCP connection, commonly because nothing listens at that address/port or an explicit reject rule exists.
- **TCP succeeds, HTTP fails:** inspect the protocol, virtual host, proxy/application logs, and HTTP response.
- **TLS failure:** verify SNI/hostname, certificate chain and dates, and that the service on the port is actually speaking TLS.
- **Works on IPv4 but not IPv6:** check AAAA, IPv6 routes, firewall policy, service bind, and provider support independently.

A timeout does not identify which firewall blocked the packet. Correlate the external result with provider rules, `sudo ufw status verbose`, `sudo ss -lntup`, service logs, and route/address inspection.

## Evidence and re-test after change

Keep a private evidence record with date, sanitized hostname, tested address family, source-network description, expected/observed result, and the relevant configuration summary. Do not publish an exact address, personal source IP, SSH username, verbose connection transcript, access token, or private key.

After each rule or listener change, repeat only the affected checks and then run the full exposure matrix. A scan is a snapshot, not a guarantee of future security; provider rules, package installs, container port mappings, and service updates can alter the attack surface. Recheck after those changes.

## Knowledge check

1. Why is a test from the VPS itself not enough to prove public exposure?
2. What does “connection refused” suggest that a timeout does not?
3. Why test IPv6 independently from IPv4?
4. Which different layers does a successful HTTPS `curl` exercise?

## Practical checkpoint

Complete [Task 06 — Prove the public exposure matrix externally](../tasks/06-prove-the-public-exposure-matrix-externally.md).
