# Task 01 — Discover and document the application runtime contract

## Outcome

Produce an evidence-backed runtime contract for `CustomerBuilderEngine-Application` that states how it is built, started, configured, connected, and persisted—without installing services or changing the VPS.

## Prerequisites

- Read [Lesson 01 — Docker’s model](../lessons/01-dockers-model-images-containers-and-the-engine.md).
- Complete the network and listener inventory in Subject 2.
- Have authorized read access to the application repository and its deployment documentation.

## Procedure

1. Record the repository URL privately, current branch/tag/commit, and the exact source revision examined. Do not put personal tokens or SSH URLs containing credentials in the evidence.
2. Read its `README` and deployment documentation. Inspect project/lock files, entry points, configuration examples, Dockerfile/Compose files if present, CI workflows, tests, and migration/start scripts.
3. Identify the supported build, test, and production start commands. Confirm which process binds to which interface and port; distinguish a container port from a host-published port.
4. List required environment variables and classify each as non-secret configuration or secret. Record names and purposes only—never production values.
5. Identify external dependencies (database, cache, object storage, mail service, worker, scheduler, or other services). Do not add a database or worker unless the repository requires one.
6. Identify stateful data paths, upload handling, migrations, background work, graceful shutdown behavior, and any architecture requirements.
7. Record the available container assets and their limitations. If the repository has no Dockerfile or supported container process, list the decisions needed from the application owner; do not invent the entry point or mark the app container-ready.

## Acceptance criteria

- [ ] The source revision and documentation examined are recorded.
- [ ] Build, test, and startup commands are supported by repository evidence.
- [ ] Each required service/dependency is classified as internal, external, or not applicable.
- [ ] Container and host port needs and expected listen address are explicit.
- [ ] Configuration names are inventoried without recording secret values.
- [ ] Persistent paths, migration behavior, and graceful shutdown requirements are documented or marked unknown.
- [ ] Any missing Dockerfile, Compose definition, health endpoint, or runtime decision is recorded as a blocking gap rather than guessed.
- [ ] No VPS configuration or public network exposure was changed during discovery.

## Deliverable

A sanitized runtime-contract record with fields for source revision, runtime/build/test commands, image assets, architecture, listening port/address, required configuration names, dependencies, persistent paths, health/readiness behavior, migrations, and unresolved questions. Keep it in the project's private engineering records; do not add credentials or production values to Git.
