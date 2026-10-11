# Task 05 — Inventory listeners and define private service paths

## Outcome

Identify every current listener, select the narrowest appropriate bind address, and document how the future reverse proxy, application, and database will communicate without unnecessary public ports.

## Prerequisites

- Read [Lesson 05 — Service binding and private container networks](../lessons/05-service-binding-and-private-container-networks.md).
- Completed Task 01's exposure plan.
- Administrative shell access to the VPS.

## Procedure

1. Capture the current listeners and process owners:

   ```sh
   sudo ss -lntup
   ```

2. For each listener, identify its package/service and purpose from local systemd/package information. Note protocol, port, bind address, expected client, and whether the service needs to exist. Do not stop or reconfigure an unfamiliar service.
3. Compare the bind address with the intended clients. For local-only administrative/test services, prefer loopback where supported. For public web traffic, the later reverse proxy is the public entry point; keep direct application and database access private.
4. Draw the planned service path: internet client → reverse proxy → application → database. Mark which hops will use loopback and which will use a private Docker network after the Docker subject.
5. For each future service, record the intended container port separately from any host-published port. State explicitly that a database port will not be published publicly and that Docker/UFW interactions must be verified in the Docker subject.
6. Do not install Docker or start public demo services as part of this task. Re-run the listener inventory after any separately approved configuration change.

## Acceptance criteria

- [ ] Every current listening socket is mapped to a known process/purpose or an unresolved investigation.
- [ ] Each planned service has an explicit client set, bind/private-path choice, and public/private decision.
- [ ] Application and database ports are not on the public allowlist without a reviewed need.
- [ ] The planned architecture has a single intended public web entry point and no assumption that UFW alone protects Docker ports.
- [ ] No unfamiliar service was stopped, and no test service was exposed just to prove connectivity.

## Deliverable

A sanitized listener inventory and a one-page service connectivity diagram/table to carry into the Docker and reverse-proxy subjects.
