# 07 — Releases, rollback, troubleshooting, and cleanup

## Learning objectives

You can deploy a specific image version, verify the running result, recover from an application-release failure, and remove unused resources without destroying persistent data.

## Make a release identifiable

Before changing production, record the currently running image reference and, where available, its image ID/digest, Compose revision, and source commit. Keep the prior known-good release available for the rollback window. Do not depend on a moving tag that may be overwritten after deployment.

An image rollback is simplest when:

- The previous image remains available from the registry or local cache.
- The Compose configuration can be changed back to the previous version.
- Runtime configuration is versioned or separately recorded without exposing secrets.
- The new application version remains compatible with the existing data format.

An image rollback does not automatically reverse database migrations or external side effects. Prefer backward-compatible expand/contract migrations and separate migration execution from simple container replacement. Define a recovery plan before a change that alters persistent data.

## Controlled release flow

For an image-based Compose deployment:

1. Select an exact, reviewed tag/digest.
2. Review the Compose diff and validate it with `docker compose config`.
3. Pull the chosen image and confirm its identity.
4. Apply the intended change to the correct Compose project.
5. Check container state, health, logs, resource use, local/private connectivity, and the public endpoint only when that ingress has been intentionally configured.
6. Record the result and retain the previous release until the rollback window closes.

Do not replace a release merely because a registry has a newer tag. A deployment is a deliberate change, not an automatic consequence of pulling.

## Troubleshoot from evidence

Start with the symptom and trace outward, rather than restarting everything:

1. `docker compose ps` — is the expected container present, running, and healthy?
2. `docker inspect` — what image, command, mounts, network, and restart state are actually configured?
3. `docker compose logs --tail=... SERVICE` — what did the application report near the failure?
4. `docker events` — was the container created, stopped, killed, or restarted?
5. `docker stats` and host `free`, `df`, `df -i` — is CPU, memory, disk, or inode pressure relevant?
6. `docker network inspect` and in-container/service tests — can the expected peer be reached?
7. `ss -lntup` and a client on an independent network — is the intended host port listening and reachable?
8. Only then restart, roll back, or change configuration, capturing the before/after evidence.

Common symptom distinctions:

| Symptom | Likely areas to investigate |
|---|---|
| Container exits immediately | Entry point/command, missing configuration, permissions, incompatible architecture, application startup logs. |
| Container runs but is unhealthy | Health-check command/path, startup grace period, app readiness, dependency availability. |
| Local request fails | Listener, container port, bind address, host mapping, proxy, application startup. |
| External request times out | DNS, provider firewall, host policy, Docker publishing/bind address, routing. |
| Container restarts under load | Resource limits, OOM events, unhandled application failure, dependency pressure. |
| Data appears lost | Wrong volume/project name, wrong mount path, permissions, container-layer storage, or application writing elsewhere. |

Avoid destructive “repair” commands until you know what object they affect. Do not remove all containers, volumes, or images to troubleshoot one service.

## Rollback procedure

1. Declare the trigger: failed readiness check, error-rate increase, failed smoke test, or another measured criterion.
2. Stop further release activity and capture the current image/configuration and relevant logs.
3. Restore the prior known-good image reference and compatible configuration.
4. Recreate only the affected service(s) using the documented Compose project and verify health and application behavior.
5. Check persistent data and migrations explicitly; do not delete or recreate volumes as a rollback shortcut.
6. Record the result, cause, and follow-up action. Re-attempt deployment only after the cause is understood.

The exact application commands and success criteria must be written for the actual application, not copied from a generic example.

## Cleanup without data loss

Commands such as `docker image prune` remove dangling images; broader forms such as `docker image prune -a` remove more unused images and can remove images needed for rollback. `docker system prune` can remove stopped containers, unused networks, and build cache; options that include volumes can delete stored data. Never run broad prune commands as routine cleanup without reviewing their scope and recording a recovery path.

Before cleanup:

- Identify the intended Compose project.
- List containers, images, networks, and volumes and establish their owners.
- Confirm which release must remain available for rollback.
- Confirm stateful data is backed up and recoverable before deleting any volume.
- Prefer removing one known disposable resource at a time.

`docker compose down` normally removes the project's containers and default network but preserves named volumes unless specifically told otherwise. Confirm behavior against the installed Compose version and exact project before execution.

## Knowledge check

1. Why can an image rollback fail to restore service after an incompatible database migration?
2. Which evidence should be captured before restarting a failed service?
3. What data or rollback capability could be lost by an aggressive prune?
4. Why should diagnosis proceed layer by layer rather than immediately recreating all services?

## Practical checkpoint

Complete [Task 06 — Publish, deploy, update, and roll back a versioned image](../tasks/06-publish-deploy-update-and-roll-back-a-versioned-image.md) and [Task 07 — Diagnose a controlled failure and clean up safely](../tasks/07-diagnose-a-controlled-failure-and-clean-up-safely.md).
