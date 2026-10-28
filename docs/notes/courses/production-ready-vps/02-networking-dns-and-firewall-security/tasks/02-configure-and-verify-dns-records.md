# Task 02 — Configure and verify the intended DNS records

## Outcome

Point the intended application hostname to the VPS using only reachable address families, then verify the authoritative and recursive answers.

## Prerequisites

- Read [Lesson 02 — DNS records and domain verification](../lessons/02-dns-records-and-domain-verification.md).
- A domain and permission to manage its DNS zone.
- The provider-confirmed public address(es) and the network-path inventory from Task 01.

## Procedure

1. Choose the hostname users will enter (for example, `app.example.com`) and record its current records and TTL. Preserve the existing zone; do not replace unrelated mail, verification, or service records.
2. Confirm whether the VPS has working public IPv4 and IPv6 routes. If IPv6 has not been tested end to end, do not create an AAAA record yet.
3. At the DNS provider, create or update only the necessary A record and, if verified, AAAA record. Use a suitable TTL for the expected change process. Do not create duplicate conflicting records.
4. Query the authoritative name server or inspect the provider's authoritative view, then query a recursive resolver and the local resolver:

   ```sh
   dig +trace app.example.com A
   dig +noall +answer app.example.com A
   dig +noall +answer app.example.com AAAA
   getent ahosts app.example.com
   ```

   Replace the example hostname. Use a trusted client/provider console; if `dig` is unavailable, use the DNS provider's record view and an equivalent resolver lookup.

5. Compare returned addresses with the intended provider allocation. Check that no stale or unintended A/AAAA record remains. Note TTL and resolver-cache delay rather than repeatedly editing the zone.
6. If no domain is available, produce a proposed record plan and document the blocker; do not invent a hostname or publish records under a domain you do not control.

## Acceptance criteria

- [ ] The chosen hostname and record purpose are documented.
- [ ] Every published A/AAAA address matches a reachable, intended VPS address.
- [ ] IPv6 is either independently verified or no AAAA record is published.
- [ ] Authoritative and recursive lookup results are recorded with TTL and the observation time.
- [ ] Existing unrelated DNS records remain intact, and evidence contains no provider credentials.

## Deliverable

A sanitized DNS change record with hostname, record type, intended address family (address redacted in public evidence), TTL, verification results, and any deferred IPv6 decision.
