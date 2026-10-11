# Task 04 — Run the application as a private Compose stack

## Outcome

Use a reviewed Compose definition to start the application and only its required dependencies, prove it responds through an internal or loopback-only path, and verify no unintended host listener was created.

## Prerequisites

- Read [Lesson 04 — Runtime configuration and operations](../lessons/04-runtime-configuration-health-resources-and-logs.md) and [Lesson 05 — Networking and Compose](../lessons/05-docker-networking-and-compose-service-operations.md).
- Completed Tasks 01–03 with a supported application image/build.
- Have an approved runtime configuration source and know which values are secret. Do not use real production secrets for a learning smoke test unless the deployment has been approved and protected.
- Have not yet enabled public application ingress; the reverse-proxy/HTTPS subject handles that later.

## Procedure

1. Select the exact Compose file and project name. Review every service, image/build, network, mount, published port, user, command, health check, restart policy, resource limit, and environment source.
2. Include only dependencies proven necessary by Task 01. Use user-defined private networks and service-name addressing between containers. Do not publish the database or backend port.
3. Do not commit the runtime `.env` file. Where it is used for non-secret local configuration, apply restrictive permissions and exclude it from Git. Use a protected, documented secret-file mechanism for secrets; understand that Docker administrators can still access container configuration/data.
4. Set only justified restart policies, health checks that can actually run in the image, and memory/CPU limits sized from available capacity and measured requirements. Configure bounded log retention using the supported Engine logging configuration.
5. Validate and inspect the effective Compose configuration (`docker compose config --quiet`, then review the rendered configuration locally for secret values). Do not share rendered output containing credentials.
6. Start the named project with `docker compose up -d`. Inspect `docker compose ps`, health status, `docker compose logs --tail=100 SERVICE`, `docker stats --no-stream`, and `sudo ss -lntup`.
7. Test the application on its intended private path. If a host mapping is necessary only for local smoke testing, bind it to `127.0.0.1` and remove it after the test. Do not open provider/host firewall rules or publish a public listener as a shortcut.
8. Stop/recreate the stack once using the documented Compose workflow, then confirm the desired configuration is still applied and the service returns to its healthy state.

## Acceptance criteria

- [ ] The running project matches the reviewed Compose file and Task 01 runtime contract.
- [ ] Only required services are present; unnecessary database/cache/worker services were not added.
- [ ] Application and data ports have no unintended host-published mapping.
- [ ] Any temporary host smoke-test mapping is loopback-only and removed after verification.
- [ ] Health state, restart policy, resource settings, and log limits have observed and documented behavior.
- [ ] Application readiness is proven using its documented endpoint or command.
- [ ] Restart/recreation succeeds without manually editing a running container.
- [ ] No production secret appears in Git, image layers, public evidence, or shared terminal output.

## Deliverable

A sanitized Compose review record with project name, service topology, image references, private/public port map, health-check and restart observations, resource/log settings, smoke-test result, and unresolved operational gaps. Keep the actual secret-bearing configuration private.
