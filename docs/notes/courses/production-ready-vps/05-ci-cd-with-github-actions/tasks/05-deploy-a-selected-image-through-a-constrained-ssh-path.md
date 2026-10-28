# Task 05 — Deploy a selected image through a constrained SSH path

## Outcome

Deploy an authorized, immutable image to the intended VPS through a narrow and reviewable interface, without rebuilding on the host or exposing application secrets to CI.

## Prerequisites

- Complete Tasks 01–04. Do not start this task with unresolved release-contract, registry, access, or recovery blockers.
- Read [Lesson 06 — Safe SSH deployment and concurrency](../lessons/06-safe-ssh-deployment-and-concurrency.md).
- Have a safe staging/test target or a production change window and a tested recovery path.

## Procedure

1. Create a server-side deployment entry point owned by an administrator and not writable by the deployment account. It must validate the expected image repository and digest format, operate only on the intended Compose project/service, and reject arbitrary paths, images, or shell commands.
2. Restrict the CI SSH identity to that operation as far as practical. Test the command as the deployment account. Verify malformed digests, a different registry/repository, extra arguments, and attempts to select an alternate Compose file are rejected.
3. Add a protected release workflow/job that depends on successful release checks and references the `production` environment. Make the selected commit and image digest visible to the reviewer. Do not let a free-form dispatch input select an arbitrary host or image.
4. Apply a production-specific concurrency group. Do not cancel an in-progress deploy; document how a newer pending release is handled and how stale manual runs are prevented from rolling back a newer release.
5. Use a verified host key and protected credential, pass only the validated image digest to the remote interface, and keep production runtime secrets on the VPS. The VPS pulls from GHCR using its separate read-only credential.
6. Run the workflow against a safe target first. Confirm it selects the expected commit/digest, makes the intended change, leaves data/ports unchanged, and does not alter host provisioning settings.
7. Review execution logs and outputs for secrets, unintended shell interpolation, excessive privileges, or sensitive infrastructure details before enabling production.

## Acceptance criteria

- [ ] The production job cannot run before required checks and environment protection rules pass.
- [ ] Only the expected image repository and digest are accepted by both workflow and server-side interface.
- [ ] The workflow cannot select arbitrary hosts, commands, Compose files, or runtime secret values.
- [ ] Production runs are serialized; in-progress deployment is not canceled by a newer run.
- [ ] Deployment pulls the CI-published image and does not build on the VPS.
- [ ] The deployment account cannot edit its trusted deployment entry point or administer unrelated host state.
- [ ] A safe-target run applies exactly the expected release and leaves persistent data and network exposure intact.

## Deliverable

A reviewed deployment workflow and server-side entry point, plus sanitized staging evidence containing workflow run, source commit, selected digest, target alias (not a public address), before/after release identity, and access/deployment result.
