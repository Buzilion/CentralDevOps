# Task 06 — Publish, deploy, update, and roll back a versioned image

## Outcome

Publish or obtain a known application image using a least-privilege registry path, deploy an exact release identifier with Compose, then rehearse returning to the prior release while preserving data.

## Prerequisites

- Read [Lesson 03 — Image identity and registries](../lessons/03-image-identity-registries-and-trusted-delivery.md) and [Lesson 07 — Releases and rollback](../lessons/07-releases-rollback-troubleshooting-and-cleanup.md).
- Completed Tasks 01–05. The application must have a supported image and registry/publishing path.
- Have permission to publish and deploy test releases; a controlled maintenance window and known-good prior version; and a rollback plan for any database/schema changes.

## Procedure

1. Build/test the selected source revision using Task 03's reviewed process. Publish through the approved registry pipeline; do not place a personal broad-scope token on the VPS.
2. Use distinct least-privilege identities for publishing and pulling when available. The VPS credential should have only image-pull rights. Store it using a protected mechanism and understand its local credential-store behavior.
3. Assign a unique version tag and record the image digest, source commit, build/test result, architecture, and registry identity. Do not move or overwrite the prior known-good release tag during the exercise.
4. Configure the Compose service to use the exact new reviewed reference. Validate the rendered configuration, pull the release, and confirm the image reference and architecture before changing the running service.
5. Deploy the release using the documented Compose project. Verify container image identity, health/readiness, logs, resource use, and an application smoke test. Capture the previously running version before change.
6. Rehearse an application-level rollback by restoring the previous image reference and redeploying the affected service. Verify the old image is running and the application passes its acceptance checks.
7. Do not run schema-destructive migrations for this exercise. If the release changes data format, stop and design/verify migration compatibility and recovery before proceeding.
8. Keep both release artifacts available through the rollback window. Revoke temporary credentials and record their owner/permissions without recording the secret itself.

## Acceptance criteria

- [ ] The deployed image's tag/digest maps to a documented source revision and successful test/build record.
- [ ] The VPS uses a pull-only credential where supported, and it is not present in source, image, logs, or command history.
- [ ] The running container is confirmed to use the expected release image.
- [ ] Post-deployment health and application acceptance checks pass.
- [ ] The prior release is restored and verified without deleting or recreating persistent volumes.
- [ ] No irreversible migration or unreviewed data change was included in the rollback rehearsal.
- [ ] Temporary access is revoked or remains protected under a documented minimum-permission policy.

## Deliverable

A private release record containing old/new image tags and digests, source revisions, build/test and post-deploy results, deployment/rollback timestamps, credential permission model, and any remaining release risks. Never record token values or production secret values.
