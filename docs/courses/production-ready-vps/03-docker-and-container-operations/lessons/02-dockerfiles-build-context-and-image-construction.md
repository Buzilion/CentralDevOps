# 02 — Dockerfiles, build context, and image construction

## Learning objectives

You can explain what a Dockerfile and build context contribute to an image, review a build for avoidable size and security risks, and distinguish build-time configuration from runtime configuration.

## Source, context, and Dockerfile

A Docker build has three important inputs:

1. The Dockerfile describes the sequence of image-building instructions.
2. The **build context** is the set of files made available to the builder.
3. Build arguments and other build options select permitted build-time variations.

The context is not automatically limited to the directory containing the Dockerfile if the command supplies a broader path. A context such as the repository root may contain local `.env` files, Git history, test output, keys, or unrelated source. Review the context before building and exclude unnecessary files with `.dockerignore`.

Example `.dockerignore` entries (adapt after examining the repository):

```dockerignore
.git
.env
.env.*
!.env.example
node_modules
bin
obj
coverage
*.log
```

Ignore rules are not a secret-management system. If a secret is sent into a build, copied into an image layer, printed during a build, or saved in build cache, deleting the file in a later layer does not reliably erase it. Never pass production secrets as ordinary Dockerfile `ARG` or `ENV` values. If a build genuinely needs a secret, use the builder's secret-mount mechanism and verify the build process does not persist or log it.

## Layers, cache, and reproducibility

Many Dockerfile instructions produce cached layers. Stable dependency manifests are commonly copied before frequently changing source files so that dependency installation can be reused. This can speed up builds, but cache is an optimization, not proof that an image is current or trustworthy.

Good image construction aims for:

- Only runtime files and required runtime dependencies in the final image.
- A multi-stage build when compilation or tooling is not needed at runtime.
- Explicit, reviewed base-image versions; avoid an unqualified or moving `latest` as the only release identity.
- Awareness of the image's target CPU architecture (for example `amd64` or `arm64`), confirmed against the deployment host; Lesson 03 covers why this matters for a successful pull and run.
- A small and intentional build context.
- Deterministic dependency installation using the project's lockfiles and supported build commands.
- A clear process, working directory, and signal handling so the application can stop gracefully.
- A non-root runtime user where the application and image support it.

Multi-stage builds separate build tools from runtime artifacts. They do not automatically make the runtime safe or small; inspect the final stage and verify which files are copied into it. Pinning a digest gives stronger base-image identity, while tags can still be useful for human-readable maintenance. A deliberate update process is needed to receive security fixes.

Do not force one generic Dockerfile onto an unknown stack. Use the repository's deployment documentation, project files, lockfiles, existing CI, and tested start/build commands from Task 01. If no supported container build exists, record the missing design decision; do not guess the production entry point.

## Runtime configuration is not build configuration

Build settings determine the artifact: source revision, dependencies, compiler options, and static assets. Runtime settings determine how that artifact behaves in a particular environment: database endpoint, credentials, feature switches, and listen address.

The same image should normally be promotable between environments without rebuilding it to inject a different password or production URL. Supply runtime configuration at deployment time through a protected mechanism. An image's metadata and layer history are inspectable; putting a secret in `ENV`, a copied config file, a build argument, or a command can expose it.

## A safe build-review loop

Before building:

1. Confirm the exact repository revision and build context.
2. Review the Dockerfile and `.dockerignore`.
3. Check that dependency lockfiles and supported build/test commands are used.
4. Confirm no secrets are in the source tree or passed as ordinary build inputs.
5. Confirm the resulting runtime user and required ports from application documentation rather than assumptions.

After building:

```sh
docker image ls
docker image inspect IMAGE:VERSION
docker history --no-trunc IMAGE:VERSION
```

`--no-trunc` prints each layer's full build command instead of a shortened one, so an unexpected instruction is not hidden by column width. Inspect image metadata and layer history for unexpected commands, environment values, files, or large layers. These commands are diagnostic aids, not a complete security audit or vulnerability scan. Run the project's tests and an application smoke test in a private, controlled environment before considering the image deployable.

## Build-time supply chain

A container image can contain vulnerabilities inherited from its base image and dependencies. A successful build means only that the build completed. Track the source revision and build process, update base images deliberately, run dependency/image analysis in the appropriate pipeline, and retain the result that was actually tested. Avoid downloading unverified binaries during a build without checking their source and integrity.

## Knowledge check

1. Why should the build context be as small and deliberate as practical?
2. Why does deleting a secret in a later Dockerfile layer not make it safe?
3. What does a multi-stage build separate, and what must still be inspected?
4. Why should environment-specific credentials be supplied at runtime rather than baked into an image?

## Practical checkpoint

Complete [Task 03 — Build and inspect a reproducible application image](../tasks/03-build-and-inspect-a-reproducible-application-image.md).
