# Task 01 — Map the VPS network path and exposure plan

## Outcome

Create a sanitized network inventory and a written allowlist that identify how clients reach the VPS and which services should be public, private, or loopback-only.

## Prerequisites

- Read [Lesson 01 — Network paths, IP addresses, and ports](../lessons/01-network-paths-ip-addresses-and-ports.md).
- Administrative access to the VPS provider panel and a shell on the VPS.

## Procedure

1. In the provider panel, identify the instance's public IPv4/IPv6 allocation, attached network/firewall controls, and any NAT or private network details. Record only sanitized labels in the deliverable.
2. On the VPS, collect read-only observations:

   ```sh
   hostnamectl
   ip -brief address
   ip route
   ip -6 route
   sudo ss -lntup
   ```

3. Compare provider and guest observations. Note whether IPv6 is allocated, routed, and currently enabled; do not publish an AAAA record based only on an allocated address.
4. Create a table for every listening service with process/purpose, transport, port, bind address, intended clients, and intended exposure. Investigate unknown listeners rather than guessing from port numbers.
5. Draw a simple client → DNS → provider firewall → host firewall → listener → application path for the eventual deployment. Identify which control is owned by the VPS provider and which is configured inside Ubuntu.
6. Mark unneeded listeners/rules as “investigate/remove in the relevant change window”; do not stop unfamiliar services as part of this inventory task.

## Acceptance criteria

- [ ] IPv4, IPv6, routing, and provider firewall status are recorded or explicitly marked unavailable/unknown.
- [ ] Every observed listening socket has an owner/purpose or a tracked investigation note.
- [ ] The planned public allowlist names protocol, port, purpose, and source where restriction is practical.
- [ ] Application and database ports are marked private unless a reviewed requirement states otherwise.
- [ ] The record contains no exact IPs, credentials, private keys, or unredacted personal source addresses.

## Deliverable

A private, sanitized VPS network inventory and exposure plan. Keep exact addressing and provider account details in an approved private system, not in a public repository.
