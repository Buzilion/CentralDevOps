# Task 03 — Publish a versioned image to GHCR

## Outcome

Publish the tested application image to GitHub Container Registry (GHCR) with least privilege, a traceable source identity, and a digest that can be deployed and retained for rollback.

## Prerequisites

- Complete Tasks 01–02 and have a working production Docker build.
- Read [Lesson 04 — Container registry and GHCR image delivery](../lessons/04-container-registry-and-ghcr-image-delivery.md).
- Confirm the GitHub repository/package access model and whether the image is private.

## Procedure

1. Confirm GHCR package naming, visibility, organization policy, repository linkage, and who is authorized to publish and pull. Prefer a private package unless the application has an explicit public-image requirement.
2. Add a publisher job triggered only by an authorized protected release path. Make it depend on the required CI checks. Grant `packages: write` only to that job; use `GITHUB_TOKEN` if the package policy supports it.
3. Build the image once from the verified source revision. Ensure the Docker build context and `.dockerignore` exclude `.env`, private files, local data, and credentials. Do not pass runtime secrets through Docker build arguments.
4. Publish a human-readable release tag and a source-commit identifier. Capture and record the image digest from the registry/build output. Do not use `latest` as the deployment selector.
5. Configure the VPS pull identity independently with only the required package-read access. Store it using the server's protected credential mechanism, not in the workflow, Compose file, shell history, or application image.
6. From the intended host or a safe test host, authenticate without echoing the token and pull the image by digest. Verify the expected architecture and startup behavior.
7. Confirm that unauthorized branches/jobs cannot publish and that the previous digest remains retained for rollback.

## Acceptance criteria

- [ ] Only the intended release context can publish; publishing waits on required CI checks.
- [ ] The publishing job has only the token permissions it needs and no SSH deployment key.
- [ ] The resulting image can be tied to the source commit and has a recorded immutable digest.
- [ ] The VPS can pull that digest with read-only package access and no secret disclosure.
- [ ] The image does not contain runtime secrets, local environment files, or production data.
- [ ] Registry retention/access settings preserve the release needed for recovery.

## Deliverable

A sanitized release record containing source commit, workflow run, GHCR image name, tags, digest, package visibility/access design, publisher permissions, pull verification, and retention policy. Do not include the token or its contents.
