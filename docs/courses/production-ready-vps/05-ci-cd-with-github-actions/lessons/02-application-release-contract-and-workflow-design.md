# 02 — Application release contract and workflow design

## Learning objectives

You can turn the application's actual runtime requirements into an explicit release contract and design the build/test/deploy boundaries without guessing the stack or installing unnecessary server services.

## Establish facts before writing YAML

The delivery workflow must match the application, not a generic template. Inspect the application's README and deployment notes, project/lock files, Dockerfile and Compose definitions, configuration examples, tests, migrations, and existing workflows. Record evidence for each conclusion. A file's presence alone does not prove a command is correct or a service is required.

Document these parts of the release contract:

| Contract area | Questions to answer |
|---|---|
| Source | Which repository, protected branch, and release mechanism identify deployable code? |
| Build | What exact reproducible command builds the release? What runtime/SDK and dependency lock files are required? |
| Verification | Which unit, integration, lint, type-check, and container checks are required, and which external services do they need? |
| Output | Is the production unit a container image, package, or another artifact? Where is it stored and how is it identified? |
| Runtime | What command/Compose service starts it? Which ports, health/readiness behavior, data stores, scheduled jobs, and resources does it need? |
| Configuration | Which settings are non-secret configuration and which are secrets? Where are production values provisioned and permissioned? |
| State changes | Are database migrations or other one-way operations required? What is the compatibility and recovery plan? |
| Operations | How is the release deployed, verified, observed, and rolled back? Who can authorize it? |

Separate build-time configuration from runtime configuration. Do not put production secrets in Docker build arguments, image layers, build logs, workflow artifacts, or a frontend bundle: those outputs may be retained or publicly observable. The release artifact should be promoted unchanged from verification to deployment. Rebuilding separately for production weakens the evidence that the deployed bytes passed the checks.

## Choose a small, explicit pipeline

A practical first pipeline has clear gates:

1. **Pull request / branch CI:** install locked dependencies, run deterministic checks, build the application, and optionally build the container. No production credentials.
2. **Release candidate:** publish a versioned artifact or container image only from an authorized revision. Record source revision and artifact identity.
3. **Production deployment:** require the approved release to exist, obtain protected environment authorization, deploy the exact artifact, and verify application health.

The boundaries may be jobs in one workflow or separate workflows. Separate workflows can clarify permissions and triggers; if split, ensure the deploy workflow verifies and deploys the intended immutable artifact rather than rebuilding from a convenient branch name. Preserve links between source commit, workflow run, image digest, release, and deployment record.

Use the narrowest practical runner and token permissions. Explicitly set a working directory if the application is in a subdirectory or monorepo. Avoid shell commands assembled from issue titles, branch names, release notes, dispatch inputs, or other untrusted text. YAML expressions interpolated into a shell script can become code; pass untrusted values through environment variables and validate them against an allowlist before use.

## Decide what "passed" means

A green workflow should correspond to defined evidence, not just a successful `docker build`. List the required checks and their authoritative commands. Decide which checks are mandatory, how flaky tests are investigated, whether tests use services such as a database, and how dependency caching is keyed. Caches speed work but are not release artifacts and must not carry secrets.

Use the application's supported health/readiness contract. A process that started or an open TCP port does not prove that dependencies are ready or requests work. If no reliable health endpoint exists, record this as a release-contract gap instead of inventing a URL.

## Practical checkpoint

Create a sanitized release-contract document covering the table above. Include repository paths and exact build/test/start commands, but no VPS addresses, credentials, or production values. Mark unknown items and resolve blockers before writing a production workflow. Complete [Task 01](../tasks/01-inspect-the-application-and-define-the-release-contract.md).

## Knowledge check

1. Why should the production deployment use the same built image that passed the release checks?
2. Which values belong in the image and which belong only at runtime?
3. Why is an application health check a stronger release signal than a running process?
4. What delivery design changes if the repository is a monorepo?

## References

- [GitHub Actions: Workflow syntax](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)
- [GitHub Actions: Using secrets in GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
