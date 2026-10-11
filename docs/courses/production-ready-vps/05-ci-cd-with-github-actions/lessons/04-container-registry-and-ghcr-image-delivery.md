# 04 — Container registry and GHCR image delivery

## Learning objectives

You can publish a private, identifiable image to GitHub Container Registry (GHCR), understand who needs read/write access, and make the VPS pull the exact image selected by the release workflow.

## Registry responsibilities

A registry stores and distributes container images; it does not run them or configure the VPS. The CI publisher authenticates to push. The production host authenticates to pull if the package is private. These are distinct principals with different needs:

```text
CI publishing job -- packages:write --> GHCR image
VPS deploy identity -- packages:read --> GHCR image by digest
```

Use the workflow's `GITHUB_TOKEN` with the narrow `packages: write` permission for publication when the package/repository linkage and organization policy permit it. Do not use a personal account token with broad scopes just because it is easier. Confirm package visibility, repository linkage, and inheritance of access in GitHub's package settings; repository access and package access can differ.

For a private image, the VPS needs a pull credential. Use a dedicated machine identity or appropriately scoped token with only package-read access, rotate it, and store it on the VPS with restrictive ownership and mode, or use another supported credential broker. Do not use a workflow `GITHUB_TOKEN` as a permanent VPS credential; it is run-scoped. Do not put a pull token in Compose YAML, a Dockerfile, command-line arguments, shell history, or logs. Use Docker's standard credential mechanism, avoid echoing tokens, and understand whether credentials are stored in plaintext by the selected credential helper. Keep registry credentials separate from SSH deployment credentials.

## Name releases and deploy by immutable identity

Tag images with a human-readable version and a source identifier, for example:

```text
ghcr.io/OWNER/IMAGE:1.4.0
ghcr.io/OWNER/IMAGE:COMMIT_SHA
```

The actual strings must match the repository owner, package name, and workflow context. A version tag can move or be republished unless policy prevents it. Record the digest returned by the publish operation and pass that digest to the deploy step:

```text
ghcr.io/OWNER/IMAGE@sha256:DIGEST
```

Do not deploy `latest` as the release selector. If tags are also required by tooling, use them for discovery, then resolve and verify the digest before deployment. Do not rebuild the image on the VPS; it should pull the release artifact that CI tested.

## Build and package hygiene

Use a deliberate Docker build context, a `.dockerignore` that excludes development output and secrets, and a multi-stage Dockerfile where appropriate. Never copy local `.env` files, credentials, SSH keys, or GitHub workspace secrets into the image. Build arguments are not secret storage: values can appear in image metadata, layers, or build output. Runtime secrets are injected by the deployment configuration using a separately secured server-side mechanism.

Authenticate the CI job only for the publish step, and only with write permission needed for that package. Authenticate the VPS only for pulling. Test that the production image can be pulled and started on the intended architecture, and that no unneeded ports are published. Package cleanup/retention policies must not delete digests still needed for rollback.

## Practical checkpoint

Publish one non-production or controlled candidate image. Record its commit tag, digest, visibility, publisher permissions, and pull method. Verify that the VPS can pull by digest without exposing the credential, and that an unauthorized context cannot publish. Complete [Task 03 — Publish a versioned image to GHCR](../tasks/03-publish-a-versioned-image-to-ghcr.md).

## Knowledge check

1. Why does the VPS need a separate read-only registry identity?
2. What is the difference between a version tag and a digest?
3. Why should registry authentication and image deployment be separate from image building?
4. Which Dockerfile and build-context choices can leak secrets into an image?

## References

- [Working with the Container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Actions: Publishing Docker images](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [Docker: Build secrets](https://docs.docker.com/build/building/secrets/)
