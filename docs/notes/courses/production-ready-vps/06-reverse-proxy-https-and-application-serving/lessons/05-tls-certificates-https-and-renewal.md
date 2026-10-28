# 05 — TLS certificates, HTTPS, and renewal

## Learning objectives

You can explain certificate validation and ACME challenge choices, configure a valid HTTPS endpoint and HTTP redirect, protect private keys, and prove that renewal is automated and operational.

## What TLS proves

TLS encrypts the connection and lets a client verify that the server controls a certificate valid for the hostname it requested and chains to a trusted authority. It does not prove that the app is secure, that the correct code is deployed, or that the server is free of compromise. The hostname in the URL, DNS destination, TLS Server Name Indication (SNI), and certificate's Subject Alternative Name (SAN) must align.

The certificate's public chain is served to clients; its private key must remain secret. Limit access to the proxy/service identity and administrators who need it. Do not commit private keys, put them into container images, paste them into tickets, or include them in course evidence. For containers, mount certificate/key material read-only where practical and manage renewal data with appropriate persistence and permissions.

## ACME challenge choices

Automated Certificate Management Environment (ACME) clients prove control of a domain before issuance:

- **HTTP-01** serves a challenge under the hostname over port 80. DNS must resolve to the validation endpoint and inbound HTTP must reach the ACME client/proxy. The challenge route must not be blocked by an unrelated redirect or auth rule. HTTP-01 does not issue wildcard certificates.
- **TLS-ALPN-01** proves control with a special TLS handshake on port 443, not an HTTP request. The challenge must reach a component configured with the ACME challenge state—often the ACME client or a proxy integrated with it. If the proxy already owns port 443, verify that the client and proxy coordinate this challenge; otherwise the client may not be able to answer on the required listener.
- **DNS-01** publishes a temporary TXT record. It can issue wildcard certificates and does not require inbound web ports for domain control, but automating it requires DNS API credentials. Scope those credentials to the smallest feasible zone/record permissions, store them securely, and do not embed them in an image or broad workflow.

Use the certificate tool's documented integration for the selected proxy. For example, Caddy can manage public certificates automatically; Nginx commonly uses Certbot or another ACME client with a carefully configured deploy/reload hook. Do not have two independent clients compete to manage the same certificate lineage.

## Safe issuance and HTTPS policy

Verify DNS A/AAAA and the challenge path before production issuance. ACME authorities enforce rate limits, so use their staging environment while testing automation and use production issuance only when ready. After issuance, verify the served chain, hostname, and date from an independent client. A certificate file existing on disk is not proof that clients receive the right certificate.

Serve HTTP only for a deliberate purpose, commonly redirecting all application traffic to HTTPS and/or answering HTTP-01. A redirect preserves the path and query, and should not loop. Keep certificate challenge handling reachable if the selected renewal method needs it. Redirect policy and ACME routing need to coexist.

Modern proxy defaults are generally preferable to hand-written cipher lists copied from an old guide. Keep the proxy and crypto libraries supported and updated. If you customize protocol versions or cipher suites, use current vendor guidance and verify compatibility; do not claim a cipher configuration is secure simply because it is verbose.

## Renewal is a production dependency

Certificates expire. Confirm what schedules renewal (systemd timer, cron, container-managed Caddy, or another mechanism), under which identity it runs, how a renewed certificate is loaded, and what happens if it fails. A successful renewal simulation is useful, but also confirm the timer/job is enabled, recent executions succeeded, and the proxy reload hook works.

Typical checks include `sudo certbot renew --dry-run` for Certbot and checking the installed service's timer/logs; commands differ by installation. Caddy's automatic certificate management is tied to its running service and persistent state. Verify the actual deployment rather than assuming a package created a working timer. Alerting belongs in the later monitoring subject, but record the present renewal status and an owner now.

## HSTS: only after HTTPS is stable

HTTP Strict Transport Security (HSTS) tells browsers to use HTTPS for future requests. Enable it only after normal certificate validation and redirects are correct. Start with a conservative max-age and no subdomain/preload commitments. `includeSubDomains` affects every covered subdomain, and preload listing is a long-lived external commitment. HSTS can make recovery from a broken HTTPS setup harder for clients that have cached the policy.

## Knowledge check

1. What does a valid certificate establish, and what does it not establish?
2. Which ACME challenge requires an inbound HTTP path, and which can support wildcard certificates?
3. Why is successful certificate issuance not enough to prove renewal readiness?
4. Why is HSTS best enabled after validating the HTTPS path?

## Practical checkpoint

Choose a single certificate lifecycle, validate from a separate client, and prove renewal behavior in [Task 04 — Issue and verify a production TLS certificate](../tasks/04-issue-and-verify-a-production-tls-certificate.md).

## References

- [Let's Encrypt: How it works](https://letsencrypt.org/how-it-works/)
- [Let's Encrypt: Challenge types](https://letsencrypt.org/docs/challenge-types/)
- [Certbot: User guide](https://eff-certbot.readthedocs.io/en/stable/using.html)
- [Caddy: Automatic HTTPS](https://caddyserver.com/docs/automatic-https)
