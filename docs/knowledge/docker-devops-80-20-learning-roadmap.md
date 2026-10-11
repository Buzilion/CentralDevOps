# Docker for DevOps: Beginner to Advanced with the 80/20 Principle

The goal is not to memorize Docker commands. It is to learn the 20% of Docker concepts that solve 80% of real deployment problems, then build toward a production-ready workflow using **Docker + Ansible + GitHub Actions + VPS**.

We'll use a practical scenario throughout: manage VPS environments for development, staging, and production, run web applications and PostgreSQL in Docker, and let GitHub Actions automate deployments while Ansible manages server configuration.

## 1. The learning roadmap

### Stage 1 — Docker fundamentals
Images, containers, registries, ports, environment variables, volumes, networks, and the essential Docker CLI.

**Outcome:** run and troubleshoot applications in containers.

### Stage 2 — Dockerfiles and image building
Base images, layers, build context, caching, multi-stage builds, `.dockerignore`, non-root users, and image optimization.

**Outcome:** build secure, small, repeatable application images.

### Stage 3 — Docker Compose and persistent data
Multi-container applications, health checks, dependency readiness, persistent PostgreSQL data, and networking.

**Outcome:** run a complete application stack on one VPS.

### Stage 4 — Ansible and server provisioning
Install Docker, configure users and permissions, create directories, deploy Compose files, and manage configuration idempotently.

**Outcome:** provision a new VPS consistently without manual setup.

### Stage 5 — GitHub Actions CI/CD
Automated testing, image builds, registry pushes, SSH access, Ansible execution, deployment verification, and rollback.

**Outcome:** deploy code changes safely without building applications on the VPS.

### Stage 6 — Production operations
Resource limits, logs, monitoring, backups, secrets, vulnerability scanning, image pinning, and recovery.

**Outcome:** operate containers reliably, not merely get them running.

**Recommended approach:** learn Stages 1–3 first, then integrate Ansible and GitHub Actions. Learning all Docker commands before building something is inefficient.

## 2. The mental model: what Docker actually does

Docker packages an application and its required runtime dependencies into an image, then runs that image as a container.

```text
Application source code
          |
          v
     Docker image
 (built from Dockerfile;
 stored in a registry)
          |
          v
  Running container
 (isolated process with
 networking and storage)
```

Think of the distinction this way:

| Concept | Practical meaning |
|---|---|
| Dockerfile | Instructions for building an image |
| Image | Immutable application template, identified by a tag or digest |
| Container | A runtime instance of an image |
| Registry | Remote storage for images, such as GHCR |
| Volume | Persistent storage managed by Docker |
| Network | Communication between containers |
| Docker Compose | Declarative configuration for a multi-container application |
| Docker Engine | Software that builds and runs containers on the host |

The most important principle is that **containers are replaceable; persistent data must live outside the container's writable layer**. Recreating a container should not destroy your database.

## 3. Lesson 1 — The essential Docker commands

You do not need to memorize dozens of commands. Start with the following core set.

### A. Run your first container

```bash
docker run --name hello-docker hello-world
```

Docker downloads the image if needed, creates a container, and runs it. Since `hello-world` exits after printing its message, the container stops.

Now inspect it:

```bash
docker ps
docker ps -a
docker images
docker logs hello-docker
docker inspect hello-docker
```

Understand the difference:

- `docker ps`: running containers.
- `docker ps -a`: running and stopped containers.
- `docker images`: images available locally.
- `docker logs`: stdout and stderr output from a container.
- `docker inspect`: detailed container configuration and state.

### B. Run a web server

```bash
docker run -d \
  --name web \
  --publish 8080:80 \
  nginx:alpine
```

Open `http://localhost:8080` in your browser.

Understanding port mapping:

```text
Your computer or VPS: port 8080
              |
              v
Docker container: port 80 (Nginx)
```

`-p 8080:80` means host port 8080 maps to container port 80.

The commands you will use frequently:

```bash
docker stop web
docker start web
docker restart web
docker rm -f web
docker pull nginx:alpine
docker exec -it web sh
```

`docker exec` is particularly useful. It lets you enter a running container to investigate its filesystem, processes, or configuration. Minimal images may not include Bash, so try `sh` first.

### C. Understand the lifecycle

```text
Image exists locally
        |
        v
docker run — create and start
        |
        v
Running container
        |
        v
docker stop — stop the process
```

Stopping a container does not normally delete it or its associated volumes.

### D. Troubleshoot using a consistent sequence

When a containerized application fails, use this sequence instead of randomly restarting it:

```bash
docker ps -a
docker logs --tail 100 web
docker inspect web
docker stats
```

Then, if it is still running:

```bash
docker exec -it web sh
```

Ask these questions in order:

1. Did the container start, or did it exit?
2. What error appears in the logs?
3. Is the application listening on the expected port?
4. Is the host port mapped correctly?
5. Can it reach its dependencies?
6. Are environment variables, permissions, or mounted files incorrect?

**Best practice:** your application's primary process should run in the foreground. Docker uses the main process's lifecycle to determine whether the container is running. Avoid wrapping everything in background processes or unnecessary shell scripts.

## 4. Lesson 2 — Build your own Docker image

Running public images is useful for learning. For real applications, you will build images from your own source code.

Create a minimal project:

```text
hello-docker/
├── app.js
├── package.json
├── Dockerfile
└── .dockerignore
```

`app.js`:

```javascript
const http = require("node:http");

const server = http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("Hello from Docker!\\n");
});

server.listen(3000, "0.0.0.0");
```

`package.json`:

```json
{
  "name": "hello-docker",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "start": "node app.js"
  }
}
```

`Dockerfile`:

```dockerfile
FROM node:22-alpine

ENV NODE_ENV=production

WORKDIR /app

COPY package.json ./
COPY app.js ./

USER node

EXPOSE 3000

CMD ["node", "app.js"]
```

`.dockerignore`:

```text
.git
node_modules
.env
.env.*
npm-debug.log
```

Build and run it:

```bash
docker build -t hello-docker:1.0 .
docker run -d --name hello-app -p 3000:3000 hello-docker:1.0
```

Test it:

```bash
curl http://localhost:3000
```

Expected response:

```text
Hello from Docker!
```

### What matters in this Dockerfile?

| Instruction | Why it matters |
|---|---|
| `FROM` | Defines the base image and runtime environment |
| `WORKDIR` | Sets the working directory inside the image |
| `COPY` | Adds files to the image |
| `ENV` | Sets default environment variables |
| `USER` | Avoids running the application as root |
| `EXPOSE` | Documents the intended container port; it does not publish it |
| `CMD` | Defines the default process to run |

### The 80/20 Dockerfile best practices

1. **Use a `.dockerignore` file.** Exclude Git history, local dependencies, credentials, and irrelevant build artifacts from the build context.
2. **Run as a non-root user.** Use a suitable unprivileged user unless the application has a specific requirement otherwise.
3. **Use multi-stage builds when appropriate.** Compile or build in one stage, then copy only runtime artifacts into the final image.
4. **Optimize layer caching.** Copy dependency manifests before source files so unchanged dependencies can be reused across builds.
5. **Use reproducible inputs.** Pin important base-image versions, lock dependencies, and use immutable image digests where stronger reproducibility is required.
6. **Never bake secrets into images.** Do not copy `.env` files, SSH keys, credentials, or tokens into an image.

One important distinction: `EXPOSE 3000` is documentation, not a firewall rule. A container can listen on port 3000 without that instruction, and it will not become reachable from the host unless you publish the port or otherwise configure networking.

## 5. Lesson 3 — Docker Compose: running a real application stack

For a VPS setup, Docker Compose is one of the most valuable concepts to learn. It lets you define an application's containers, networks, volumes, and configuration declaratively in a YAML file.

Instead of manually running five `docker run` commands, you define the desired state once and manage it consistently.

Consider this architecture:

```text
Reverse proxy (Caddy or Nginx)
             |
             v
     +---------------+
     |   Web app     |
     +---------------+
             |
        app-network
             |
     +---------------+
     |  PostgreSQL   |
     +---------------+
             |
       named volume
```

The reverse proxy receives external traffic; the app communicates with the database over an internal Docker network.

### A practical Compose file

Create `compose.yaml`:

```yaml
services:
  app:
    image: ${APP_IMAGE:?APP_IMAGE must be set}
    restart: unless-stopped
    environment:
      NODE_ENV: production
      PORT: "3000"
      DATABASE_URL: ${DATABASE_URL:?DATABASE_URL must be set}
    expose:
      - "3000"
    networks:
      - app-network
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  app-network:

volumes:
  postgres-data:
```

This is an illustrative starting point, not a complete production security configuration. The application must actually use the supplied database URL and port, and the PostgreSQL image version should be chosen and tested for your application's compatibility.

### Important concepts

**1. Service names become DNS names.**

From the `app` container, the database hostname is `db`, not `localhost`.

```text
DATABASE_URL=postgresql://appuser:password@db:5432/appdb
```

Inside a container, `localhost` refers to that same container. This is one of the most common sources of Docker networking errors.

**2. `expose` is not `ports`.**

- `expose`: documents an internal service port; it does not publish it to the host.
- `ports`: publishes a container port on the host.

For example, a public web service might use:

```yaml
ports:
  - "127.0.0.1:8080:3000"
```

That allows a reverse proxy running on the VPS host to reach the app on port 8080. It does not expose that port on the VPS's external network interface.

**3. Volumes preserve database data.**

The named volume `postgres-data` survives container replacement. Deleting the container does not normally delete the named volume, but explicitly removing volumes can destroy the data.

**4. Health checks improve readiness handling.**

A running container does not necessarily mean its application is ready. `depends_on` with `service_healthy` delays app startup until the database passes its health check. Your app should still handle temporary database disconnections and reconnect when necessary.

### Commands worth mastering

```bash
docker compose config
docker compose pull
docker compose up -d
docker compose ps
docker compose logs -f app
docker compose exec app sh
docker compose restart app
docker compose down
```

Understand this distinction:

- `docker compose up -d`: reconciles the declared services with the desired configuration.
- `docker compose down`: stops and removes the Compose-managed containers and networks; named volumes are retained unless you explicitly request their removal.
- `docker compose down -v`: also removes associated declared named and anonymous volumes. **Do not run this casually on production.**

**Best practice:** keep the Compose file in version control. Use environment-specific configuration for dev, staging, and production rather than manually changing the server's configuration each time.

For PostgreSQL, never treat a Docker volume as a backup. Back up the database separately, store copies outside the VPS, and test restoration.

## 6. Lesson 4 — Docker architecture for your VPS environments

For a cost-conscious deployment with separate dev, staging, and production environments, start with one Docker Engine per VPS and isolated Compose projects.

```text
Development VPS
└── Docker Engine
    └── dev Compose project
        ├── dev app
        └── dev database

Staging VPS
└── Docker Engine
    └── staging Compose project
        ├── staging app
        └── staging database

Production VPS
└── Docker Engine
    └── production Compose project
        ├── production app
        └── production database
```

The benefit of separate VPS environments is that staging configuration errors or resource consumption are less likely to affect production.

If you later consolidate environments on one VPS, use distinct Compose project names, volumes, networks, credentials, and ports. But remember that containers on the same Docker host share the host's kernel and resource pool. Compose project separation alone is not a strong security boundary.

### How I would structure your DevOps repository

```text
devops/
├── ansible.cfg
├── inventory/
│   ├── dev/
│   │   └── hosts.yml
│   ├── staging/
│   │   └── hosts.yml
│   └── production/
│       └── hosts.yml
├── playbooks/
│   ├── bootstrap-vps/
│   │   └── bootstrap.yml
│   ├── configure-docker/
│   │   └── docker.yml
│   └── deploy-app/
│       └── deploy.yml
├── roles/
│   ├── common/
│   ├── docker_engine/
│   ├── firewall/
│   └── compose_app/
├── apps/
│   └── example-app/
│       ├── compose.yaml
│       └── env/
│           └── production.env.example
└── .github/
    └── workflows/
        ├── provision-vps.yml
        └── deploy-app.yml
```

This is a reasonable starting structure, not a mandatory standard. Keep application-specific Dockerfiles with their application source repository unless you have a clear reason to centralize them. The DevOps repository should primarily own infrastructure configuration, deployment definitions, and reusable automation.

## 7. Lesson 5 — Ansible's responsibility versus Docker's responsibility

This separation is fundamental to a maintainable deployment system.

**Ansible manages the host and deployment configuration. Docker runs the application.**

| Responsibility | Best fit |
|---|---|
| Create a VPS | Cloud provider API or provisioning tool |
| Configure SSH, users, firewall, and packages | Ansible |
| Install and configure Docker Engine | Ansible |
| Create deployment directories and permissions | Ansible |
| Build an application image | CI workflow, usually GitHub Actions |
| Push an image to GHCR | GitHub Actions |
| Pull an image onto the VPS | Docker, orchestrated by Ansible |
| Start or update Compose services | Ansible + Docker Compose |
| Persist and back up database data | Docker volumes + database backup automation |
| Verify deployment health | CI/CD workflow and runtime monitoring |

### Example: install Docker using Ansible

For a real deployment, use the official Docker Engine installation instructions for your OS and a maintained Ansible role or tasks that configure Docker's official package repository. Avoid blindly running an installation script as root.

An illustrative playbook:

```yaml
- name: Configure Docker hosts
  hosts: docker_hosts
  become: true

  roles:
    - docker_engine
```

Your `docker_engine` role would contain tasks for installing the supported Docker packages, enabling the service, and configuring any required daemon settings.

For example, the role might use:

```yaml
- name: Ensure Docker is running
  ansible.builtin.service:
    name: docker
    state: started
    enabled: true
```

This task is idempotent: repeated runs maintain the desired state rather than blindly repeating a one-time action.

### Example: deploy a Compose application using Ansible

A simplified task file could look like this:

```yaml
- name: Create application directory
  ansible.builtin.file:
    path: /opt/example-app
    state: directory
    owner: root
    group: root
    mode: "0750"

- name: Install Compose configuration
  ansible.builtin.template:
    src: compose.yaml.j2
    dest: /opt/example-app/compose.yaml
    owner: root
    group: root
    mode: "0640"

- name: Pull and start application
  community.docker.docker_compose_v2:
    project_src: /opt/example-app
    pull: always
    state: present
```

This example assumes the Docker Engine and the required Compose plugin are installed, the collection is available, and required environment variables and registry credentials have already been configured. A production implementation should also handle secrets, health verification, and failed-deployment recovery.

The `community.docker.docker_compose_v2` module belongs to the `community.docker` collection; it is not part of `ansible-core`.

### Three Ansible practices to learn early

1. **Idempotency:** running the same playbook twice should not introduce unintended changes.
2. **Variables and templates:** separate environment-specific settings from reusable tasks.
3. **Handlers:** trigger a restart or reload only when a task changes relevant configuration.

For Docker, don't restart the entire Engine every time you deploy a new application image. Usually, update the affected Compose service instead.

## 8. Lesson 6 — GitHub Actions + Ansible + Docker CI/CD

This is where the concepts come together.

```text
1. Push code to GitHub
          |
          v
2. CI: test and validate
          |
          v
3. Build and publish image
   GitHub Actions → GHCR
   Tag with commit SHA
          |
          v
4. Deploy via SSH + Ansible
   Pull/update Compose services
          |
          v
5. Verify deployment health
   If failed, stop rollout and recover
```

### Why build on GitHub Actions instead of the VPS?

Your VPS resources are limited. Building on the CI runner:

- Keeps CPU and RAM available for running applications.
- Separates the build environment from the runtime environment.
- Produces an artifact that can be tested before deployment.
- Lets staging and production deploy the same image.

**The key rule: build once, promote the same image.** Do not independently rebuild staging and production from the same source commit. They could end up running different artifacts if dependencies or base images change.

### Use immutable image tags

A Git commit SHA is a practical image tag:

```text
ghcr.io/your-org/your-app:a1b2c3d4e5f6
```

The exact SHA would be generated by the workflow. Configure Compose to use a variable:

```yaml
services:
  app:
    image: ${APP_IMAGE:?APP_IMAGE must be set}
    restart: unless-stopped
```

Ansible can deploy the desired image reference as an environment variable or through a carefully managed configuration file.

Avoid relying on `latest` for production. It doesn't tell you which version you deployed and makes rollback less reliable. For stronger artifact identity, record and deploy the image digest as well.

### How GitHub Actions connects to your VPS

1. **Create a dedicated deployment key pair.** Generate a key pair for the CI deployment identity. Store the private key in GitHub Actions secrets and install its public key in the appropriate VPS user's `authorized_keys`.
2. **Configure the inventory.** Ansible inventory identifies each host's address, SSH user, and connection settings. The host must already be reachable over SSH.
3. **Run Ansible from the GitHub Actions runner.** The runner loads the private key, verifies the VPS host key, selects the target inventory, and runs the deployment playbook.

A new VPS cannot be reached by a key that hasn't been installed yet. You solve this with a bootstrap process:

1. Provision the VPS through the provider.
2. Establish trusted initial access using a cloud-init-provisioned key, a provider-supported access mechanism, or another secure bootstrap path.
3. Run Ansible to configure the deployment user, SSH policy, firewall, and Docker.
4. Use the resulting host as a deployment target for future workflows.

Ansible does not magically create SSH connectivity; the initial trust and access path must exist first.

### SSH best practices

- Use separate deployment identities or keys for different trust boundaries, particularly production.
- Restrict private key access to the workflows and environments that require it.
- Pin and verify SSH host keys; do not disable host key checking just to make CI pass.
- Avoid giving the deployment user unrestricted root access if a more constrained model is practical.
- Protect production deployments with GitHub environment approvals and branch protections.
- Never commit private keys, passwords, or production `.env` files into the repository.

### GitHub Actions example: build and push an image

This is a simplified build workflow for a repository containing a Dockerfile at its root.

```yaml
name: Build image

on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ghcr.io/your-org/your-app:${{ github.sha }}
```

This illustrates the core flow, not a fully hardened production workflow. Replace the placeholder image name with your actual lowercase GHCR path, add your test and validation steps, and review action versions and permissions before adopting it. For stronger supply-chain security, pin actions to reviewed commit SHAs and add provenance or signature verification where appropriate.

For a private GHCR image, the VPS also needs appropriate registry pull credentials. Do not assume the GitHub Actions `GITHUB_TOKEN` automatically gives your VPS permission to pull private packages.

### Deployment workflow: trigger Ansible

The deploy job can check out your DevOps repository and run Ansible against the intended inventory. For example:

```yaml
- name: Install Ansible dependencies
  run: |
    python -m pip install ansible
    ansible-galaxy collection install community.docker

- name: Deploy to staging
  env:
    ANSIBLE_HOST_KEY_CHECKING: "True"
  run: |
    ansible-playbook \
      -i inventory/staging/hosts.yml \
      playbooks/deploy-app/deploy.yml \
      --limit staging
```

This assumes the inventory exists in the checked-out DevOps repository, the SSH private key has already been loaded, host keys are configured, and the image reference and secrets are provided securely.

In a real pipeline, use a controlled deployment environment and pass the exact image SHA produced by the build job. Use job dependencies such as `needs: build`, and require staging validation before production deployment.

## 9. Lesson 7 — Production practices that prevent expensive mistakes

These are the areas where a beginner's Docker setup typically becomes unreliable.

| Topic | Recommended practice |
|---|---|
| Secrets | Inject at runtime; use protected secrets or a secrets manager |
| Database persistence | Named volumes plus independent, tested backups |
| Networking | Publish only required ports; keep databases private |
| Container privileges | Run non-root where possible; avoid privileged containers |
| Image versions | Pin versions and promote immutable artifacts |
| Restart policy | Use an appropriate policy, but don't mistake restarts for health management |
| Health checks | Verify application readiness and dependencies |
| Logs | Write application logs to stdout/stderr and centralize them |
| Resource usage | Monitor CPU, RAM, disk, and container restarts; configure limits where appropriate |
| Updates | Recreate affected services deliberately; understand migrations and compatibility |
| Rollbacks | Retain previous image references and define database recovery separately |
| Backups | Store off-host and test restoration regularly |

### Two subtle but important production lessons

**A successful container start is not proof of a successful deployment.** The application might be unable to connect to PostgreSQL, return HTTP 500, or fail to serve real traffic. Verify application-level health.

**Rolling back an image does not automatically roll back a database schema.** If a deployment runs destructive migrations, an older image may no longer work with the new schema. Prefer backward-compatible migrations and explicit recovery plans.

For a single VPS, Docker Compose is usually sufficient. You do not need Kubernetes just because you're learning DevOps. Consider an orchestrator only when your actual requirements justify its additional operational complexity.

## 10. Your practical learning exercises

Complete these in order. Each exercise builds a skill you'll use in your eventual deployment pipeline.

### Exercise 1 — Run and inspect containers
**Estimated time:** 30 minutes

- Run an Nginx container and publish a port.
- Inspect its logs, state, and port mappings.
- Stop and remove the container.

### Exercise 2 — Build a custom image
**Estimated time:** 45–60 minutes

- Create the Node.js app and Dockerfile from Lesson 2.
- Build and run the image.
- Change the response and rebuild the image.

### Exercise 3 — Deploy with Compose
**Estimated time:** 60–90 minutes

- Run an app and PostgreSQL together.
- Connect the app using the database service name.
- Recreate the database container and verify the data persists.

### Exercise 4 — Provision a VPS with Ansible
**Estimated time:** 1–2 hours

- Configure an inventory and SSH access.
- Install Docker using an Ansible role.
- Run the playbook twice and inspect whether the second run makes unnecessary changes.

### Exercise 5 — Automate deployment
**Estimated time:** 2–4 hours

- Build and push an image to GHCR from GitHub Actions.
- Deploy its commit-SHA tag using Ansible.
- Verify the application and demonstrate rollback to a previous image.

## 11. The 80/20 summary

If you remember only these principles, remember these:

1. **Images are artifacts; containers are runtime instances.**
2. **Use Dockerfiles to build your application, and Compose to define multi-container applications.**
3. **Keep persistent data outside replaceable containers.**
4. **Use Docker networks and service names for internal communication.**
5. **Use Ansible for repeatable server configuration and deployment orchestration.**
6. **Use GitHub Actions to test, build, publish, and trigger deployment.**
7. **Build once and promote the same immutable image through environments.**
8. **Treat SSH access, secrets, image provenance, backups, and rollback as part of deployment design—not optional finishing touches.**
9. **Verify application health after every deployment.**
10. **Learn Docker Compose and single-host operations thoroughly before considering Kubernetes.**

**Recommended next step:** start with Lessons 1–3 and complete the first three exercises on your local machine. Once you understand containers, images, volumes, and Compose, the Ansible and GitHub Actions integration will make much more sense.
