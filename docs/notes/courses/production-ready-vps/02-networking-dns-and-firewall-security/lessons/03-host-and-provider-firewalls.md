# 03 — Host and provider firewalls

## Learning objectives

You can define a minimal inbound allowlist, distinguish provider filtering from a host firewall, configure UFW without losing administrative access, and verify both IPv4 and IPv6 policy.

## Two enforcement points

A provider firewall filters traffic before it reaches the VPS guest. A host firewall filters packets within the guest. Either can block a connection; neither should be assumed to configure the other. Some providers have multiple network products or default policies, so inspect the actual instance and its attached network.

For a small public web server, the eventual inbound set is often SSH plus HTTP/HTTPS, but the exact ports and sources depend on the deployment design. A database normally does not need an internet-facing rule. Before the reverse proxy is installed, keep HTTP/HTTPS closed unless a current, verified purpose requires them. Outbound policy is a separate decision; do not copy an inbound allowlist and assume it describes outbound needs.

Use default-deny inbound behavior and allow only the intended protocol, destination port, and—where practical—source range. A source restriction is helpful only if the source address/range is stable and you have a recovery route when it changes. Avoid exposing administrative services to `0.0.0.0/0` merely for convenience.

## UFW on Ubuntu

UFW (Uncomplicated Firewall) is a frontend for host packet-filtering rules. First inspect the current rules and the actual SSH port:

```sh
sudo ufw status verbose
sudo ss -lntp
sudo sshd -T | grep -i '^port '
```

The standard OpenSSH package may provide an `OpenSSH` application profile, but confirm it exists with `sudo ufw app list`. A safe pattern is to add the SSH allow rule **before** enabling UFW:

```sh
sudo ufw allow OpenSSH
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw status numbered
```

If SSH uses a nonstandard port, add an explicit rule for its actual TCP port (and an appropriate source if you have a stable administrative range), not a guessed default. Review rules, ensure provider-level policy permits your test client, retain an existing session, and validate a second SSH session before relying on a changed policy. Then enable the firewall:

```sh
sudo ufw enable
sudo ufw status verbose
```

Do not paste an unfamiliar rule sequence into a production shell. Understand each rule and the current default policies first. UFW rules can include IPv6 when UFW's IPv6 support is enabled; check `/etc/default/ufw` for `IPV6=yes` and inspect `sudo ufw status verbose`. If IPv6 is in use, test it from outside rather than assuming an IPv4 test covers it.

Add public web rules only when there is a listener and a reason to serve public traffic:

```sh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

The command above is an example for the later web-serving phase, not a requirement to open those ports now. Prefer provider and host rules that express the same intended public exposure. Recheck the final rules after every change.

## Stateful filtering and rate limits

Host firewalls commonly track connection state, so response traffic for allowed outbound connections is treated differently from unsolicited inbound traffic. This does not mean every outbound connection should be allowed forever; outbound controls can be tightened once application dependencies are understood.

`ufw limit` can rate-limit repeated new connection attempts to a service. It is not a substitute for key-based authentication, SSH daemon policy, a provider firewall, or log-based brute-force protection. A tool such as Fail2ban can act on repeated authentication failures, but it must be installed, configured for the active logging backend, and monitored. Lesson 04 covers SSH-specific controls.

## Docker caveat

Docker can install packet-filtering/NAT rules for published container ports. Depending on the Docker and UFW configuration, a port published by Docker may be reachable despite a UFW rule that appears to deny it. Therefore, do not use UFW alone as the boundary for container ports. Later, publish only the reverse proxy publicly; keep application and database services on private container networks or bind host-published development ports to loopback. Verify from an external client and follow the Docker version's networking documentation.

## Verification and safe change management

After a firewall change:

1. Read back the active rules (`ufw status verbose` and the provider firewall configuration).
2. Confirm the SSH service is still listening and keep a known-good session open.
3. Open a fresh SSH connection from the intended client.
4. Test expected public ports from a genuinely separate network.
5. Check IPv4 and IPv6 independently if both are enabled.

An internal probe from the VPS does not establish what the internet can reach. Use provider console/recovery access if remote administration is lost; do not repeatedly make blind changes over the only session.

## Knowledge check

1. Why are provider and host firewalls separate controls?
2. Why must an SSH allow rule be in place before enabling UFW remotely?
3. Why can Docker-published ports require special attention even when UFW is active?
4. What does `ufw limit` not replace?

## Practical checkpoint

Complete [Task 03 — Apply and prove a minimal firewall policy](../tasks/03-apply-and-prove-a-minimal-firewall-policy.md).
