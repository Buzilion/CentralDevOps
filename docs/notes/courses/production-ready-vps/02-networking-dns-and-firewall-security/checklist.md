# Networking, DNS, and Firewall Security — Course Checklist

Complete this subject after **Linux Server Administration** and before installing Docker or deploying the application. Make remote access changes only after confirming provider console/recovery access and a second working SSH session. Keep evidence sanitized: do not commit exact IP addresses, hostnames, personal source addresses, usernames, logs containing identifying details, or credentials.

## Lessons

- [ ] [01 — Network paths, IP addresses, and ports](lessons/01-network-paths-ip-addresses-and-ports.md)
- [ ] [02 — DNS records and domain verification](lessons/02-dns-records-and-domain-verification.md)
- [ ] [03 — Host and provider firewalls](lessons/03-host-and-provider-firewalls.md)
- [ ] [04 — SSH hardening and brute-force defense](lessons/04-ssh-hardening-and-brute-force-defense.md)
- [ ] [05 — Service binding and private container networks](lessons/05-service-binding-and-private-container-networks.md)
- [ ] [06 — External verification and network troubleshooting](lessons/06-external-verification-and-network-troubleshooting.md)

## Hands-on tasks

- [ ] [Task 01 — Map the VPS network path and exposure plan](tasks/01-map-the-vps-network-path-and-exposure-plan.md)
- [ ] [Task 02 — Configure and verify the intended DNS records](tasks/02-configure-and-verify-dns-records.md)
- [ ] [Task 03 — Apply and prove a minimal firewall policy](tasks/03-apply-and-prove-a-minimal-firewall-policy.md)
- [ ] [Task 04 — Harden SSH and prove a safe second login](tasks/04-harden-ssh-and-prove-a-safe-second-login.md)
- [ ] [Task 05 — Inventory listeners and define private service paths](tasks/05-inventory-listeners-and-define-private-service-paths.md)
- [ ] [Task 06 — Prove the public exposure matrix externally](tasks/06-prove-the-public-exposure-matrix-externally.md)

## Subject completion gate

- [ ] I can trace a request through DNS, provider networking, the host firewall, a listening socket, and the application.
- [ ] I can distinguish an address, route, transport protocol, port, socket, and application protocol.
- [ ] DNS records match reachable addresses; I do not publish AAAA records until IPv6 is verified end to end.
- [ ] Provider-level and host-level firewall rules have been reviewed independently.
- [ ] The inbound policy is default-deny with only documented, necessary services permitted.
- [ ] I can explain how UFW, provider filtering, service binding, and Docker port publishing interact.
- [ ] SSH uses a verified key-based non-root administrative login, and a separate recovery path is available.
- [ ] I can distinguish DNS failure, timeout, connection refusal, HTTP failure, and TLS validation failure.
- [ ] External tests confirm only intended public services are reachable; application and database ports are not unnecessarily exposed.
- [ ] All six tasks are complete and their credential-free, sanitized evidence is retained privately.

## Exit criteria

Continue to **Docker and container operations** only when every lesson and task is checked, every public listener is explained, external exposure matches the written allowlist, and the SSH recovery procedure is known. If the domain or IPv6 is not available yet, record the dependency and keep the corresponding record or service unpublished; do not weaken firewall policy to work around it.
