# 02 — Domain, DNS, firewall, and listener preflight

## Learning objectives

You can establish whether the domain, address families, firewall, and upstream listener are ready before publishing HTTPS, and can distinguish a DNS failure from a network, proxy, or application failure.

## Preflight dependencies

Before requesting a public certificate or opening web access, identify:

- A domain and hostname you control, and the DNS provider that is authoritative for it.
- The VPS's current public IPv4 and, only if configured and tested, public IPv6 addresses.
- Provider firewall rules and host firewall rules, including IPv4 and IPv6 behavior.
- The proxy's planned listeners and the verified application upstream address/port.
- A recovery route such as provider console access if a firewall change interrupts SSH.

Create A and AAAA records only for address families that work from end to end. An AAAA record that points to an address with no functioning route, listener, or firewall allowance can break access for IPv6-preferring clients even while IPv4 appears healthy. A CNAME target must resolve correctly. DNS TTL controls cache lifetime, not instantaneous propagation.

## Port 80 and 443 are separate decisions

TCP 443 is required for normal HTTPS. TCP 80 is often intentionally open to redirect users to HTTPS and to support ACME HTTP-01 certificate validation. If you use DNS-01 validation, port 80 may not be needed for certificate issuance, but it may still be a product choice for redirecting ordinary HTTP traffic. Publish only ports with a documented role. Keep SSH policy separate, and do not open the application/database ports to “make the proxy work.”

Review both provider-level firewall rules and host-level rules. A host rule alone cannot correct an upstream provider firewall block. Similarly, an `ss` listener output describes the host, not what an external network can reach. Docker port publishing may install packet-filter rules with behavior that differs from a simple UFW rule; verify exposure from a separate network.

## Inspect resolution and listeners

Use placeholders until replacing them with your controlled hostname and intended port:

```sh
dig +noall +answer app.example.com A
dig +noall +answer app.example.com AAAA
getent ahosts app.example.com
sudo ss -lntp
sudo ufw status verbose
```

The exact DNS client and firewall commands depend on the operating system and DNS provider. Check the provider panel for authoritative records, and query both a recursive resolver and the authoritative source when diagnosing discrepancies. For IPv6, inspect the provider's IPv6 allocation and firewall separately.

Test the application upstream on the VPS before involving the proxy. A host-based app might be queried on loopback; a container app may be reachable by Compose service name from the proxy's container network. The URL, path, and response must match the application's documented readiness or known route. Do not expose the upstream publicly as a debugging shortcut.

## A layered diagnosis

```text
Hostname wrong/unresolved      -> DNS records, delegation, cache, A/AAAA
Connection times out/refused   -> route, provider firewall, host firewall, listener
Proxy returns 502/504          -> proxy-to-upstream path, app health, timeout
Wrong page / 404               -> Host/path routing, app base path, static/API behavior
TLS name/date/trust error      -> certificate name/chain/validity, SNI, clock
```

One successful layer does not prove the next. For example, `curl` to `127.0.0.1` proves only local HTTP connectivity; it does not prove DNS, public firewall access, certificate validation, or external reachability.

## Change safety

Before firewall changes, keep an existing administrative session open and confirm console access. Apply a narrow rule, inspect the resulting policy, then test from an independent client. Avoid locking out SSH by changing its port/policy without a tested second login. At this stage, exposing 80/443 should happen only when the proxy is ready to serve a deliberate response.

## Knowledge check

1. Why should an AAAA record be withheld until IPv6 is proven end to end?
2. Which parties may independently filter a connection to the VPS?
3. What does a local upstream `curl` establish—and what does it not establish?
4. Why might a Docker-published port be reachable despite assumptions based only on UFW?

## Practical checkpoint

Complete [Task 02 — Prove DNS, firewall, and origin preconditions](../tasks/02-prove-dns-firewall-and-origin-preconditions.md) before requesting a public certificate.

## References

- [Let's Encrypt: Challenge types](https://letsencrypt.org/docs/challenge-types/)
- [Docker: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [IANA: Service Name and Transport Protocol Port Number Registry](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml)
