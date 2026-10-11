# 03 — Image identity, registries, and trusted delivery

## Learning objectives

You can distinguish a human-readable image tag from immutable image identity, explain how registries and credentials fit into delivery, and select a release identifier that supports verification and rollback.

## Image names and identity

An image reference commonly contains a registry, namespace or owner, repository, and tag:

```text
ghcr.io/OWNER/APP:VERSION
```

The exact components vary by registry. A **tag** such as `1.4.2` is a name that can be moved to point at a different image. `latest` is also just a tag; it has no built-in meaning that guarantees the image is recent, tested, or safe. An image **digest** identifies content by hash, for example `...@sha256:...`, and is immutable for that content.

For production, select a deliberate release identifier and retain a record tying it to source revision, build, tests, and deployment. Pinning a digest can ensure the VPS runs the exact image content that was approved. Human-readable version tags remain useful, but ensure your publishing policy does not silently replace a release tag.

## Registries and trust boundaries

A registry is a distribution service, not a validation service. Pulling an image successfully does not prove who built it, which source revision it contains, or whether it passed tests. Pull images only from the intended namespace, verify the reference, and use the project’s approved publishing path.

A typical delivery flow is:

```text
reviewed source revision
    -> build and test
    -> publish a versioned image
    -> record its tag/digest
    -> VPS pulls that exact release
    -> verify the running container
```

The VPS does not need a source checkout or build toolchain merely to run an already-built image. Separating build from deployment reduces what must be installed on the server and clarifies which artifact is being promoted.

## Registry authentication

Use separate permissions for publishing and pulling where supported. A CI publisher should have only the rights needed to publish the intended package; the VPS needs only read/pull permission. Prefer short-lived or narrowly scoped credentials. Do not reuse a personal account's broad token as a deployment credential.

Docker login credentials may be stored in the user's Docker configuration. Without an appropriate credential helper, they may be stored in a form that is recoverable by someone with access to that account. Protect the account home directory and credential files; configure an appropriate credential store where the environment supports it. Avoid putting tokens directly in command-line arguments, shell history, Compose files, logs, or repository secrets.

For interactive login, pass a secret through standard input rather than typing it as a command argument:

```sh
printf '%s' "$REGISTRY_TOKEN" | docker login ghcr.io --username "$REGISTRY_USER" --password-stdin
```

This is a syntax example, not a recommendation to export a long-lived token in a shell session. Use the credential-delivery mechanism appropriate to your environment, keep values out of recorded terminal output, and log out or revoke credentials when no longer needed. Do not print the token to verify it.

## Architecture and platform

An image is built for one or more target CPU architectures and operating systems. Confirm that the published image supports the VPS architecture (for example, ARM64 versus AMD64) or that the build system produces a suitable multi-platform image. A successful pull does not always mean the image can start on this host.

Keep the image promotion path explicit: the tested artifact should be the artifact deployed. Avoid rebuilding independently on the VPS after a CI-tested image was published, because that changes the artifact and can make incident analysis and rollback ambiguous.

## Verification limits

Record at least:

- Repository and release tag/digest.
- Source commit or build identifier.
- Test/build result and when it was produced.
- Target architecture.
- Registry/package visibility and credential owner.
- The exact reference configured for the VPS.

Image signatures, provenance attestations, and vulnerability scanning can strengthen this chain if supported by your registry and build pipeline. Their presence must be verified and policy-enforced; a label or green scan alone is not a guarantee of safety.

## Knowledge check

1. Why is `latest` not a reliable release strategy?
2. What guarantees does a digest provide that a tag does not?
3. Why should the server's pull credential be separate from the CI publisher credential?
4. Why is a successful image pull not proof that the image is trusted or runnable?

## Practical checkpoint

Complete [Task 06 — Publish, deploy, update, and roll back a versioned image](../tasks/06-publish-deploy-update-and-roll-back-a-versioned-image.md).
