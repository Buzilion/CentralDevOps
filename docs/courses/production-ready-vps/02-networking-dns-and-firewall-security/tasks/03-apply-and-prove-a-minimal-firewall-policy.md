# Task 03 — Apply and prove a minimal firewall policy

## Outcome

Configure a default-deny inbound host firewall and align provider firewall rules with the smallest required set, without losing SSH access.

## Prerequisites

- Read [Lesson 03 — Host and provider firewalls](../lessons/03-host-and-provider-firewalls.md).
- Completed Task 01's network inventory.
- Verified provider console/recovery access and a known-good SSH account/key.
- A maintenance window; do not make the first firewall change while depending on the only SSH session.

## Procedure

1. Inspect current policy, SSH port/listener, UFW application profiles, and IPv6 setting:

   ```sh
   sudo ufw status verbose
   sudo ufw app list
   sudo ss -lntp
   grep '^IPV6=' /etc/default/ufw
   ```

2. In the provider control panel, review the current inbound/outbound firewall policy and identify how to restore it through the console.
3. Decide the minimal required inbound entries from Task 01. Add the actual SSH TCP port/source before enabling UFW. If SSH uses the packaged profile, confirm `OpenSSH` exists before using it.
4. Set default incoming deny and the currently justified outbound policy. Retain required provider control-plane services and application dependencies; do not block outbound traffic without understanding impact.
5. Review `sudo ufw status numbered`, then enable UFW only after confirming the SSH rule and recovery route. Keep the original session open and establish a second SSH session.
6. Add HTTP/HTTPS rules only if they are intentionally needed now; otherwise leave them closed until the reverse proxy phase. Ensure IPv6 rules are represented when IPv6 is enabled.
7. Align provider rules with the same intended exposure and document differences that are deliberate.

## Acceptance criteria

- [ ] Incoming default policy is deny and every allowed inbound rule has a documented purpose.
- [ ] SSH remains reachable in a second, newly established session.
- [ ] Provider and host policy are both inspected and their intended relationship is recorded.
- [ ] Unneeded application/database ports are not allowed from the public internet.
- [ ] IPv6 behavior is checked or explicitly documented as not enabled/not available.
- [ ] Console/recovery access is known, and no changes were made without a rollback path.

## Deliverable

A sanitized firewall policy record listing protocol, port, source scope, purpose, provider/host rule location, and verification result. Do not include exact admin source IPs in public evidence.
