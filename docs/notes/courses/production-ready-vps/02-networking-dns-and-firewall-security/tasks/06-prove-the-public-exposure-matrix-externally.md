# Task 06 — Prove the public exposure matrix externally

## Outcome

Test each intended and unintended public TCP endpoint from outside the VPS, verify DNS and address-family behavior, and retain clear evidence of the resulting attack surface.

## Prerequisites

- Read [Lesson 06 — External verification and network troubleshooting](../lessons/06-external-verification-and-network-troubleshooting.md).
- Completed Tasks 01–05.
- A workstation or other independent client network; provider console access for recovery.

## Procedure

1. Freeze the expected-exposure matrix from Tasks 01 and 03. For a pre-proxy server, SSH may be the only intended public TCP service; do not open ports 80/443 simply to make the test matrix look complete.
2. Resolve the intended hostname and record A/AAAA answers and TTL:

   ```sh
   dig +noall +answer HOSTNAME A
   dig +noall +answer HOSTNAME AAAA
   ```

3. From a separate network, test the actual SSH port and each intentionally open web port with a TCP probe (PowerShell `Test-NetConnection HOST -Port PORT`, or a platform-equivalent tool). Test expected-closed application/database ports as well. Do not scan systems or addresses you are not authorized to test.
4. If IPv6 is enabled or published, repeat the checks over IPv6. Distinguish “no IPv6 record/address” from “published but unreachable.”
5. For any configured HTTP(S) endpoint, make an application-layer request. For HTTPS, verify normal certificate validation; do not bypass it. If no web endpoint is configured yet, record this as deferred and keep its ports closed.
6. Compare observations with provider rules, `sudo ufw status verbose`, `sudo ss -lntup`, and the listener inventory. Investigate every unexpected open port and every expected port that is closed; change only the responsible layer.
7. Re-run affected checks after a correction and save sanitized timestamped evidence: source-network type, address family, expected result, observed result, and disposition.

## Acceptance criteria

- [ ] Tests were initiated from a client outside the VPS, not only from loopback or the server itself.
- [ ] Every expected public endpoint has a recorded result; every intentionally closed application/database endpoint is unreachable externally.
- [ ] IPv4 and IPv6 results are independently represented whenever applicable.
- [ ] DNS, TCP, HTTP, and TLS outcomes are not conflated; unresolved stages have an investigation note.
- [ ] No unexpected public listener remains unexplained or untracked.
- [ ] Evidence contains no credentials, private keys, exact private client IPs, or raw verbose transcripts.

## Deliverable

A dated, sanitized external-reachability report and the final public-exposure matrix. Preserve the test method so it can be repeated after Docker, proxy, firewall, or service changes.
