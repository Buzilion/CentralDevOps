# Task 04 — Issue and verify a production TLS certificate

## Outcome

Serve a certificate valid for the intended hostname, redirect ordinary HTTP safely, and prove the selected certificate-renewal mechanism is scheduled and functional.

## Prerequisites

- Complete Task 03.
- Read [Lesson 05 — TLS certificates, HTTPS, and renewal](../lessons/05-tls-certificates-https-and-renewal.md).
- Confirm DNS, firewall, and selected ACME challenge prerequisites. Use a controlled domain.

## Procedure

1. Choose one certificate manager and one challenge type. Record the required DNS/network conditions and the identity that will own renewal. Do not let multiple clients manage the same certificate lineage.
2. Validate hostname records and the challenge path. Use the ACME staging environment for initial integration testing to avoid production rate limits.
3. Issue/install the certificate using the proxy/vendor-supported procedure. Verify private key ownership and permissions; ensure key material is not in Git, an image, a workflow log, or course evidence.
4. Configure HTTPS for the intended hostname and HTTP-to-HTTPS behavior. Preserve path and query in the redirect. Keep HTTP-01 reachable if that is the renewal method.
5. Reload only after native configuration validation. From an independent client, request the hostname with a normal validating TLS client; verify the SAN, chain, dates, and expected HTTP response without disabling verification.
6. Inspect the real scheduler (service timer, cron, or proxy-managed mechanism), its last execution/log, and its privilege. Run the supported dry-run/simulation, then verify that the deploy/reload hook is usable.
7. Test redirect behavior for the root and a representative nested path/query. Confirm no loop and no mixed-content or incorrect HTTP absolute URLs caused by proxy-scheme trust.
8. Enable HSTS only after the above succeeds. Begin conservatively; do not add `includeSubDomains` or preload unless every affected name and operational consequence has been reviewed.

## Acceptance criteria

- [ ] The certificate SAN covers the exact public hostname and is within its validity period.
- [ ] An independent client validates the served chain without insecure/bypass options.
- [ ] HTTP redirects to the intended HTTPS URL without losing path/query or looping.
- [ ] The chosen challenge and renewal prerequisites remain satisfied.
- [ ] Renewal automation is enabled, the dry-run/simulation succeeds, and proxy reload behavior is known.
- [ ] Private key permissions are restricted and no key material is recorded in evidence or source control.
- [ ] HSTS policy, if enabled, has an explicit scope and does not accidentally commit unready subdomains to HTTPS.

## Deliverable

A sanitized TLS verification record, renewal/scheduler evidence, and a short certificate-expiry/renewal recovery note.
