# 05 — Docker networking and Compose service operations

## Learning objectives

You can explain how Compose groups services, distinguish private container connectivity from host-published ports, and inspect the resulting topology before making the stack reachable to users.

## Networks and service discovery

Containers attached to the same user-defined Docker network can normally reach each other using service names and container ports. For example, an application service can connect to a database using a hostname such as `db` and the database's listening port. The database does not need a host port mapping just because another container needs to use it.

Docker networking is an additional path beside the host network. A firewall policy written before Docker is installed may not express the whole exposure policy after ports are published. The actual behavior depends on the Docker Engine, network driver, host configuration, and provider firewall. Avoid treating a UFW rule as the only control on a published container port.

Use the smallest needed network membership. A reverse proxy and application may share a private network; a database should only join networks used by the services that need it. Multiple networks can separate front-end and data paths. Container name-based discovery is convenient but does not replace authentication, TLS where needed, or application-level authorization.

## Host port publishing

Compose `ports` creates host-to-container port publishing. It is appropriate for intentionally public ingress or a bounded local diagnostic. `expose` documents a container port for other services but does not publish it on the host; it is not a complete access-control boundary.

For local-only verification, publish to loopback explicitly:

```yaml
ports:
  - "127.0.0.1:18080:8080"
```

Do not add a mapping such as `"8080:8080"` for convenience without understanding which host interfaces will accept connections and how Docker interacts with the host firewall. In a production architecture, a reverse proxy will generally be the public entry point; application and database traffic stays private. Only publish public web ports when the reverse proxy and network phase is ready.

After creating a stack, inspect both Docker and host state:

```sh
docker compose ps
docker network ls
docker network inspect PROJECT_NETWORK
docker port CONTAINER
sudo ss -lntup
```

Then test from a different machine/network for any intended public listener. A successful loopback request proves only the local path.

## Compose as an application definition

Compose is a declarative YAML format plus CLI workflow for defining related services, networks, volumes, configuration, and operational settings. It is not a general-purpose secret manager or full production orchestrator.

A simplified structural example (not an app-specific file) illustrates the distinction between an internal service and an intentionally published entry point:

```yaml
services:
  app:
    image: registry.example.invalid/team/app:REPLACE_WITH_REVIEWED_VERSION
    networks:
      - app-private
    restart: unless-stopped
    # Add only the runtime settings confirmed by the application contract.

  database:
    image: postgres:REPLACE_WITH_REVIEWED_VERSION
    networks:
      - app-private
    volumes:
      - database-data:/var/lib/postgresql/data
    restart: unless-stopped
    # Do not publish the database port to the host.

networks:
  app-private:

volumes:
  database-data:
```

The placeholder registry is intentionally non-routable, and the snippet is not ready to deploy. A real database image, path, health check, secret strategy, compatibility matrix, and application settings must be selected from supported project documentation. The roadmap's application might not need a database container at all; do not add one simply because a common template includes it.

Before starting a project, ask Compose to validate and render the effective configuration:

```sh
docker compose config --quiet
docker compose config
```

`--quiet` only validates the file and exits non-zero on error; the plain form also prints the fully rendered configuration for review. The rendered output may include resolved values; do not paste it into a public ticket if it contains secrets. Review the exact project directory and project name: Compose uses those to determine which containers, networks, and volumes a command targets.

## Compose operations

Run lifecycle commands from the directory containing the intended Compose file, or explicitly specify the file and project name. This reduces the risk of operating on the wrong stack.

```sh
docker compose ps
docker compose up -d
docker compose logs --follow SERVICE
docker compose stop SERVICE
docker compose start SERVICE
docker compose down
```

`up` may create, start, or recreate containers to match the definition. `stop` retains containers; `down` removes project containers and its default network. Named volumes are normally retained unless a volume-removal option is explicitly requested. Always inspect the command's scope before using destructive flags. Avoid multiple unrelated stacks sharing an ambiguous project name.

## Knowledge check

1. How can the app reach a database without publishing the database port on the host?
2. What is the operational difference between Compose `ports` and `expose`?
3. Why is `docker compose config` useful before running a stack?
4. Why can UFW alone be an insufficient check of Docker port exposure?

## Practical checkpoint

Complete [Task 04 — Run the application as a private Compose stack](../tasks/04-run-the-application-as-a-private-compose-stack.md), then prove persistence and connectivity in [Task 05](../tasks/05-prove-data-persistence-and-private-service-connectivity.md).
