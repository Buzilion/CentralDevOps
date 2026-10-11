# Task 01 — Inspect the application and define the release contract

## Outcome

Create an evidence-based description of how `CustomerBuilderEngine-Application` is built, tested, configured, started, and safely released. Resolve unknowns before adding production credentials or a deploy workflow.

## Prerequisites

- Complete Subjects 01–04, especially the Docker image and Compose tasks.
- Have authorized read access to `CustomerBuilderEngine-Application`.
- Read [Lesson 01 — Workflow model, triggers, runners, and trust boundaries](../lessons/01-workflow-model-triggers-runners-and-trust-boundaries.md) and [Lesson 02 — Application release contract and workflow design](../lessons/02-application-release-contract-and-workflow-design.md).

## Procedure

1. Inspect the README/deployment notes, project and lock files, Dockerfile/Compose files, configuration examples, migrations, tests, and existing `.github/workflows/`.
2. Run the documented dependency install, test, and production build locally or in the already established safe development environment. Record exact commands and tool versions; do not invent a successful command from filenames.
3. Identify application entry point, listening port/bind address, health/readiness behavior, required backing services, persistent data, scheduled/background work, and architecture requirements.
4. Classify every configuration value as non-secret runtime configuration, secret runtime configuration, or build-time non-secret value. Identify where production secrets will be provisioned on the VPS without copying them into CI.
5. Document database migration behavior, whether old and new releases can coexist with the schema, and the manual recovery decision if a migration or health check fails.
6. Select the release unit (prefer the tested container image if the app already supports it), registry, immutable release identity, production deployment mechanism, verification condition, and rollback approach.
7. List unknowns and blockers. Do not enable deployment until each production-critical item has an owner and resolution.

## Acceptance criteria

- [ ] Exact runtime/toolchain, install, test, build, and start commands are recorded with evidence.
- [ ] Required services, ports, health/readiness behavior, persistent state, and migration behavior are identified.
- [ ] No assumptions are made about the language, database, port, or health URL without repository/runtime evidence.
- [ ] Build-time inputs and runtime secrets are distinguished; no secret value is recorded.
- [ ] The release artifact, identity, publisher, deployer, production configuration location, verification, and rollback are stated.
- [ ] Any unresolved production-critical question blocks deployment rather than being hidden in a generic workflow.

## Deliverable

A reviewed, sanitized release contract (for example, `docs/deployment/release-contract.md` in the application repository) with links to the source files/commands inspected and an explicit list of assumptions and open decisions. Never include credentials, actual secret values, private keys, or identifying VPS details.
