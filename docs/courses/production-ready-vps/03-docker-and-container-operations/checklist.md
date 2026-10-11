# Docker and Container Operations — Course Checklist

Complete this subject after **Networking, DNS, and Firewall Security**. It assumes you have a working administrative login, a known recovery path, and a written network exposure plan. Use the application repository to discover its actual runtime requirements; do not infer a language, database, or deployment topology. Keep evidence sanitized and never commit credentials, production environment values, private registry tokens, or identifying server details.

## Lessons

- [ ] [01 — Docker’s model: images, containers, and the engine](lessons/01-dockers-model-images-containers-and-the-engine.md)
- [ ] [02 — Dockerfiles, build context, and image construction](lessons/02-dockerfiles-build-context-and-image-construction.md)
- [ ] [03 — Image identity, registries, and trusted delivery](lessons/03-image-identity-registries-and-trusted-delivery.md)
- [ ] [04 — Runtime configuration, health, resources, and logs](lessons/04-runtime-configuration-health-resources-and-logs.md)
- [ ] [05 — Docker networking and Compose service operations](lessons/05-docker-networking-and-compose-service-operations.md)
- [ ] [06 — Persistent data, volumes, and safe storage handling](lessons/06-persistent-data-volumes-and-safe-storage-handling.md)
- [ ] [07 — Releases, rollback, troubleshooting, and cleanup](lessons/07-releases-rollback-troubleshooting-and-cleanup.md)

## Hands-on tasks

- [ ] [Task 01 — Discover and document the application runtime contract](tasks/01-discover-and-document-the-application-runtime-contract.md)
- [ ] [Task 02 — Install Docker Engine and verify its security boundary](tasks/02-install-docker-engine-and-verify-its-security-boundary.md)
- [ ] [Task 03 — Build and inspect a reproducible application image](tasks/03-build-and-inspect-a-reproducible-application-image.md)
- [ ] [Task 04 — Run the application as a private Compose stack](tasks/04-run-the-application-as-a-private-compose-stack.md)
- [ ] [Task 05 — Prove data persistence and private service connectivity](tasks/05-prove-data-persistence-and-private-service-connectivity.md)
- [ ] [Task 06 — Publish, deploy, update, and roll back a versioned image](tasks/06-publish-deploy-update-and-roll-back-a-versioned-image.md)
- [ ] [Task 07 — Diagnose a controlled failure and clean up safely](tasks/07-diagnose-a-controlled-failure-and-clean-up-safely.md)

## Subject completion gate

- [ ] I can distinguish an image, a running container, a registry, a volume, a network, and the Docker daemon.
- [ ] I understand that containers share the host kernel and that access to the Docker daemon is effectively privileged host access.
- [ ] The runtime contract reflects observed application files and commands, not assumptions about the stack.
- [ ] Images are built from a reviewed context, do not contain secrets, run as a non-root application user where supported, and have an identifiable version.
- [ ] The VPS pulls a deliberate image version; production does not depend on `latest` or an unreviewed local build.
- [ ] Environment configuration and registry authentication are protected and are not baked into the image or committed to Git.
- [ ] Compose describes the services, networks, storage, and operational settings needed to reproduce the intended stack.
- [ ] Only the intended public entry point is published; application and data services remain on private paths.
- [ ] Health checks, restart behavior, resource controls, and bounded logs are configured and their limits are understood.
- [ ] Persistent data survives container replacement; volume persistence is not mistaken for a backup.
- [ ] A version change and application rollback have both been rehearsed without deleting persistent data.
- [ ] I can inspect container state, logs, events, resource use, listeners, and Compose configuration to isolate a failure.
- [ ] Cleanup preserves application data and the image required for rollback.
- [ ] All seven tasks have measurable, credential-free evidence retained in a private operations record.

## Exit criteria

Continue only when every lesson and task is checked, the actual application stack has a documented runtime contract, and the deployment can be reproduced and safely rolled back. If the application lacks a reviewed Dockerfile, Compose definition, or container-compatible runtime contract, record that as a blocking dependency rather than improvising a production image. Do not expose application or database ports to make a local test pass. Treat backups, public HTTPS ingress, monitoring, and automated deployment as separate subjects; this course does not claim to complete them.
