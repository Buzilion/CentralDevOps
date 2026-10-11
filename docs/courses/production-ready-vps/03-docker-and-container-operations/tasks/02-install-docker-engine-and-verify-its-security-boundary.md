# Task 02 — Install Docker Engine and verify its security boundary

## Outcome

Install and validate Docker Engine and the Compose plugin on the intended Ubuntu VPS, document the access model, and prove that a known test container runs without exposing a service publicly.

## Prerequisites

- Read [Lesson 01 — Docker’s model](../lessons/01-dockers-model-images-containers-and-the-engine.md).
- Completed Subject 1 and Subject 2, including a known-good second SSH session and provider console/recovery path.
- Confirmed the VPS distribution/version and architecture; this task's package examples are for Ubuntu/Debian-family systems only.
- Completed Task 01 and checked that the required runtime is suitable for container operation.

## Procedure

1. Capture the current OS release, architecture, disk space, memory, and current listeners. Check the provider console and SSH recovery path before package or firewall work.
2. Review any existing Docker/container runtime installation, package sources, and services. Do not remove packages or stop unfamiliar services as a shortcut; identify conflicts and choose a reviewed migration path.
3. Follow Docker's current official instructions for the VPS distribution to configure its signed package repository and install Docker Engine, CLI, containerd, Buildx, and the Compose plugin. Verify repository signing and package origin. Do not execute an unreviewed remote install script as root.
4. Start/enable the Engine using the distribution's service manager only after reviewing package changes. Confirm the daemon is healthy with `sudo systemctl status docker --no-pager`, `sudo docker version`, and `sudo docker info`.
5. Verify Compose is available with `sudo docker compose version`. This is the Compose v2 plugin syntax; do not assume the legacy standalone `docker-compose` command is installed.
6. Run `sudo docker run --rm hello-world` to verify image pull, container creation, execution, and automatic removal. This test does not expose an inbound service.
7. Initially use `sudo docker ...`. If choosing to add an account to the `docker` group, document that group as effectively root-equivalent and justify exactly which person/service needs that access. Do not grant it to a general application or CI account as a convenience.
8. Review whether the daemon socket is private and whether any TCP listener exposes the Docker API. Keep the API local and protected; do not publish it to the internet. Record the impact of Docker-published ports on the host firewall plan before exposing any application.

## Acceptance criteria

- [ ] Docker Engine packages come from the distribution-appropriate, signed official repository and the installed versions are recorded.
- [ ] Engine and Compose plugin versions are available and the service is healthy after boot.
- [ ] The `hello-world` check succeeds and leaves no running test container.
- [ ] No unauthenticated Docker API is listening on a network interface.
- [ ] Access to the Docker socket is restricted; no unsafe world-writable permission was applied.
- [ ] Docker group membership is either absent or documented as privileged with a justified minimum member list.
- [ ] SSH and the existing network policy remain functional; no demo service was published.
- [ ] Package changes, recovery route, and remaining hardening needs are recorded without secrets.

## Deliverable

A private installation record listing OS/architecture, package source and installed versions, service/Compose verification, daemon access decision, group membership, API exposure review, and test result. Do not include authentication material or full server identifiers in public evidence.
