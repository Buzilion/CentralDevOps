# Task 03 — Build and inspect a reproducible application image

## Outcome

Build an identifiable image from the reviewed application revision, run the project's applicable tests, and document evidence that the build context and final image do not include accidental secrets or unnecessary build inputs.

## Prerequisites

- Read [Lesson 02 — Dockerfiles and image construction](../lessons/02-dockerfiles-build-context-and-image-construction.md).
- Completed Task 01 with build/test commands and a reviewed Dockerfile/build strategy.
- Docker Engine and Buildx are available on the chosen build machine. A build machine may be the VPS for this learning exercise, but production should prefer building once in a controlled CI/build environment and promoting that same artifact.

## Procedure

1. Check out the exact source revision recorded in Task 01. Confirm a clean/understood working tree and identify the actual build context and Dockerfile path.
2. Review the Dockerfile and `.dockerignore`. Exclude local environment files, Git metadata, test/build output not needed by the image, credentials, and unrelated repository content.
3. Check that the build uses the project's lockfiles and supported production build command. Review base-image version, final-stage contents, runtime user, startup command, exposed container port metadata, and architecture.
4. Confirm no secret value is present in source, build arguments, `ENV`, copied config, or build logs. If a build-time secret is required, use a supported secret mount and verify it is not persisted in image layers/cache.
5. Build with a non-`latest` local identifier tied to the source revision or a unique course version. Example shape (replace every placeholder with the repository's actual values):

   ```sh
   docker build --file PATH/TO/Dockerfile --tag LOCAL_IMAGE:SOURCE_VERSION PATH/TO/CONTEXT
   ```

6. Run the repository's tests and, if documented, an isolated smoke test. Keep any diagnostic port loopback-only and do not insert real production secrets.
7. Inspect the result with `docker image inspect`, `docker history --no-trunc`, and `docker image ls`. Check image architecture, size, environment metadata, layers, labels, and configured command. Review command output locally before sharing it.
8. If the repository has no supported Dockerfile/build procedure, stop before inventing one. Complete the gap list and obtain an application-specific containerization decision; mark this task blocked until that prerequisite is resolved.

## Acceptance criteria

- [ ] The build is traceable to the exact source revision and uses a reviewed context.
- [ ] A reviewed `.dockerignore` excludes local secrets and irrelevant files.
- [ ] Application tests pass for the selected build; test results are recorded.
- [ ] The image runs as a non-root user where supported, with a documented exception if not.
- [ ] No secret is baked into image metadata or layers, and no production secret is used in a test.
- [ ] The image architecture and required runtime command/port are consistent with Task 01.
- [ ] The image reference is not an unqualified/moving `latest` tag.
- [ ] Any unaddressed image/build security gap is recorded rather than hidden by a successful build.

## Deliverable

A private build record containing source revision, Dockerfile/context, exact build command with secret values omitted, image tag/ID/digest, architecture/size, test and smoke-test result, runtime user, and outstanding findings. If blocked, provide the specific repository-level changes or decisions required to proceed.
