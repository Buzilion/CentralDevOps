# 04 — Runtime configuration, health, resources, and logs

## Learning objectives

You can inspect and configure a container's runtime, explain the difference between a process restart and an application health check, and collect useful diagnostics without leaking secrets.

## Runtime configuration

Runtime configuration includes the command, user, environment, mounted files, network attachments, published ports, resource limits, and restart behavior. Changing a container's configuration generally requires it to be recreated; restarting it does not rewrite its environment or port mapping.

Prefer an explicit non-root process user when the application supports it. The UID/GID must be able to read required files and write only to the paths that need persistence or temporary data. Do not solve a permissions problem by making the entire host directory world-writable.

Environment variables are convenient, but they are not automatically secret storage. Values may be visible to privileged host users, Docker API clients, process inspection, or support bundles. Do not use them for sensitive values unless the threat model and platform are understood. Use a protected runtime secret mechanism (for example, a tightly permissioned file mounted read-only or a supported Compose secret) where appropriate. Local Compose secrets are mounted files, not a general-purpose encrypted vault; protect the source file, host, backups, and deployment access.

Configuration belongs in reviewed Compose/service definitions when it is non-secret. Keep secret-bearing files out of version control, apply restrictive ownership and permissions, and never print secret-bearing configuration into logs or troubleshooting output.

## Ports and process lifecycle

A container port is not necessarily a host port. Compose `ports` publishes a mapping from the host to the container; omitting a mapping normally leaves the service un-published on the host. Bind a local test mapping to loopback when only local testing is needed:

```yaml
ports:
  - "127.0.0.1:18080:8080"
```

Replace ports with values confirmed from the application contract. Do not bind a backend directly to `0.0.0.0` merely because it needs to be reachable by a reverse proxy; connect the proxy and backend over a private Docker network instead. Published Docker ports can interact with firewall behavior; verify actual listeners and external exposure rather than relying on UFW rules alone.

Containers should run the application as the foreground process, receive termination signals correctly, and shut down within the configured grace period. Shell wrappers that do not `exec` the application can interfere with signal delivery. A database or web server running as PID 1 inside a container is still a process; Docker does not automatically make its lifecycle graceful.

## Health checks and restart policies answer different questions

A **health check** asks whether a process or endpoint appears ready/healthy according to a test. Choose a test that reflects the application's real readiness and can run inside the image (or use an external checker). A TCP socket open is weaker than an application-level readiness check, and a liveness check should not fail merely because an optional dependency has a brief issue.

A **restart policy** governs whether a container process is started again after exit or daemon restart. It is not an application repair mechanism and does not guarantee that unhealthy containers are replaced. In Compose, a health status can influence startup ordering when a supported `depends_on` condition is used, but startup ordering is not ongoing dependency orchestration.

Plan explicitly what happens when a health check fails: alert, inspect logs, restart manually, or use an orchestrator with a designed remediation policy. Avoid restart loops that conceal a persistent configuration or data failure.

## Resource controls

Containers share host capacity. Consider memory, CPU, process counts, and storage when choosing limits. Memory exhaustion can cause the kernel to kill a process; an apparently random restart may be an out-of-memory event. CPU limits can protect neighbors but may increase request latency. Disk use includes writable layers, volumes, image layers, build cache, and logs.

Set limits using measured application behavior and VPS capacity, leaving room for the OS, Docker, reverse proxy, database, and operational tasks. A limit that is too low can make a service unstable; no limit can let a runaway workload starve the host. Verify the effective configuration and observe actual use after load testing.

## Logging and first-line inspection

The container's stdout/stderr is commonly collected by Docker. The application should emit useful, timestamped, appropriately structured logs to those streams. Do not log passwords, tokens, session cookies, personal data, or full secret configuration. Configure log retention/rotation appropriate to the Engine's logging driver; unbounded container logs can fill a VPS disk.

Useful diagnostics:

```sh
docker compose ps
docker compose logs --tail=100 SERVICE
docker inspect CONTAINER
docker stats --no-stream
docker events --since 30m
sudo ss -lntup
```

Review outputs before sharing them: `inspect`, environment dumps, and application logs may contain sensitive values. `docker exec` is useful for narrowly scoped inspection, but it changes the running container's state if you modify files and should not become an undocumented deployment method.

## Knowledge check

1. Why does a restart policy not replace a health check or alert?
2. What is the difference between a container port and a published host port?
3. Why can environment variables fail to meet a strict secret-protection requirement?
4. Name two ways container logs can cause operational harm if left unmanaged.

## Practical checkpoint

Complete [Task 04 — Run the application as a private Compose stack](../tasks/04-run-the-application-as-a-private-compose-stack.md).
