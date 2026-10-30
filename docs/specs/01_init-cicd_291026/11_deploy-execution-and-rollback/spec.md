# Spec 11: Deploy Execution and Rollback

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 11 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation gated on completion of specs 04, 07, 08 and 10 |
| Depends on | `04_docker-and-deploy-runtime`, `07_routing-and-tls`, `08_shared-database` and `10_deploy-authorization` (each checklist must be complete before implementation) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `central-deployment-v1.md` (`DEP`), `routing-and-tls-v1.md` (`RTE`), `database-v1.md` (`DB`), `access-and-secrets-v1.md` (`SEC`), `registry-and-policy-v1.md` (`REG`), and `app-release-v1.md` (`REL`) in `docs/prd/01_init-cicd_291026/` |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§5–7; `docs/design/naming-and-repository-conventions.md` §§3–6; `docs/design/variables-and-secrets.md` §§2–4; v5 design §§8.2–8.5, 9.2–9.4, 10.3, 11.3, 13.4, 15.3, 15.6 and 16 step 9 |

## What

Complete the privileged `deploy` stage in the CentralDevOps `deploy-app.yml` workflow. After spec 10 authorizes the request and completes its preflight, deploy the exact immutable image digest through the restricted `cdo-deploy` account and root-owned `centraldevops-deploy` entrypoint. Serialize host changes, preserve the previous release, provision the registry-owned database contract when enabled, run an optional release command before replacement, check container health, and automatically restore the previous release when that health check fails.

After health passes, integrate with spec 07's route entrypoint, run the external HTTPS smoke test, and record the final outcome. Produce a secret-free host deployment record, a central Actions run summary, a safe result handoff for spec 12, an operations runbook and Staging acceptance evidence.

## Context and sequencing

- This spec may be implemented only after the checklists for specs 04, 07, 08 and 10 are complete. Writing spec 11 does not bypass roadmap order: spec 09 has been authored, and spec 10 still needs to be generated and completed before implementation.
- Spec 10 owns request authentication, replay rejection, registry/manifest/Compose preflight, runtime-key validation and the resolved deployment plan. This spec consumes only that authorized plan; it does not reinterpret raw dispatch inputs as trusted app, Environment, host, digest or path values.
- Spec 04 creates the restricted deploy account, sudo boundary and fail-closed `/usr/local/sbin/centraldevops-deploy` and `/usr/local/sbin/centraldevops-route` entrypoints. Preserve their paths, root ownership, non-deploy-writable permissions and least-privilege boundary.
- Spec 06 owns registry and Compose schemas and policy. Spec 08 owns the database provisioner and its credential-rotation rollback interface. Spec 11 integrates these contracts; it must not add another policy or database authority.
- Spec 07 owns route rendering, the shared proxy lock, route rollback on invalid Nginx configuration and the `apply`/`confirm` interface. This spec calls that interface only after app health passes.
- The Q8 decision in spec 07 is binding: a failed post-activation HTTPS smoke test fails the run but does not automatically roll back the app or route. DEP-12 automatic rollback applies to a container health-check failure before route activation.
- Spec 12 owns the app-side `request-deploy` action and `deploy.yml`. DEP-15 requires both run summaries to carry the DEP-14 metadata fields; spec 12's current polling draft lists only Environment, digest, central URL and result. The sanitized handoff defined here must be consumed by spec 12, and that summary contract must be reconciled before implementation.
- Spec 13 owns off-host backup and restore. This spec owns the host record location and format and must hand that path to spec 13 for backup inclusion. DEP-14's off-host restore criterion is not complete until spec 13 proves it.
- The initial deployment remains a single-host `docker_edge` rollout with a brief interruption. Blue/green deployment and automatic database-schema rollback are out of scope.

## Requirements

| ID | Priority | Statement | Source |
|---|---|---|---|
| DEP-08 | Must | Staging deploys without manual approval. The Production deploy job binds to the validated CentralDevOps `Production` Environment and waits for its approval after request verification but before using Environment secrets or connecting to a host. A delayed approval does not invalidate the already-verified source request. | DEP PRD DEP-08; v5 §8.2 |
| DEP-09 | Must | Host-side locks serialize deployments of the same app and Environment and serialize proxy edits/reloads across apps. A deployment from one app cannot cancel another app's pending deployment. | DEP PRD DEP-09; RTE PRD RTE-11; v5 §8.2, §8.4 |
| DEP-11 | Must | Use the restricted deploy identity to pull the exact digest, render the approved runtime configuration, replace the containers and wait for the configured health check (default 90 seconds). | DEP PRD DEP-11; v5 §8.3 |
| DEP-12 | Must | On a post-replacement health-check failure, restore the previous release and leave the route unchanged. If this is the first deployment, leave the app stopped. | DEP PRD DEP-12; parent PRD NFR-05; v5 §8.4 |
| DEP-14 | Must | Every authorized host deployment attempt writes a secret-free record with app, Environment, requested and previous digest, source commit and run, central run URL, UTC time and result. Store it on the host and include it in off-host backups. | DEP PRD DEP-14; v5 §13.4 |
| DEP-15 | Must | Produce a sanitized summary for the central run and a machine-readable result handoff that spec 12 can use for the app-run summary. Never print runtime environment contents. Both summaries contain the DEP-14 metadata fields and no secret value. | DEP PRD DEP-15; v5 §8.3 |
| DEP-17 | Must | Correlate deploy-account SSH/sudo audit events and the host deployment record with the source app run and central run, without logging secret values. | DEP PRD DEP-17; v5 §8.5 |
| DEP-18 | Must | Document failure diagnosis and recovery: inspect central/app/container logs, keep the route unchanged on health-check rollback, rerun with a previous known-good digest when appropriate and record the cause. Exercise the runbook on Staging. | DEP PRD DEP-18; v5 §15.6 |
| DEP-19 | Should | If the validated manifest declares `release_command`, run it exactly once in a one-off container with the new image before replacement. Failure aborts replacement and leaves the current release serving. | DEP PRD DEP-19; v5 §11.3 |
| RTE-07 | Must | Run the HTTPS smoke test from the runner after route activation, show the result in the run summary and fail the run when it fails. Per spec 07's Q8 decision, do not automatically roll back the app or route for this failure. | RTE PRD RTE-07; spec 07 |
| RTE-11 | Must | Use spec 07's shared proxy lock so different app deployments cannot edit or reload the proxy simultaneously. | RTE PRD RTE-11; v5 §8.4 |
| SEC-12 | Must | Keep secret values out of workflow logs, summaries and artifacts; mask secret values and never upload temporary decrypted bundle contents. | SEC PRD SEC-12; v5 §§8.3, 12.3 |

## Design

### Workflow handoff and approval

- Extend the existing `.github/workflows/deploy-app.yml`; spec 10 remains the owner of the `authorize` and preflight stages. The `deploy` job runs only when authorization succeeds and uses the resolved app, Environment, host and digest from that job's outputs.
- Bind the privileged job to the validated Environment output, not the raw `target_environment` dispatch field. Staging has no manual approval. Production approval is supplied by the CentralDevOps `Production` Environment and must happen before the job reads `DEPLOY_SSH_PRIVATE_KEY` or `DEPLOY_RUNTIME_AGE_PRIVATE_KEY`, decrypts the bundle or opens SSH.
- Verify the source identity token before the approval wait in spec 10. Do not reject an otherwise authorized request merely because that token expires while a human is deciding whether to approve the Production job.
- Run the workflow only from a ref allowed by the selected Environment (any branch for `Staging`, `release/*` only for `Production`) and check out the workflow revision for that run. Use least-privilege permissions and the matching Environment's credentials only.
- Use a separate workflow concurrency group keyed by the resolved app and Environment, with `cancel-in-progress: false`. Do not use one Environment-wide group: one app's dispatch must not replace another app's pending run. GitHub concurrency is scheduling only; server-side locks remain the correctness control.

### Restricted host execution and locking

- Connect only to the single host resolved by the authorized plan, using the matching Environment's deploy key, pinned host keys and strict SSH host-key checking. Never accept a host, SSH user, inventory path, command or filesystem path from app-controlled input.
- Send only the validated files and required non-secret attempt metadata to the host. The root-owned `centraldevops-deploy` entrypoint revalidates every argument and input file, rejects unsafe paths, symlinks, malformed fields and unexpected keys, and uses the derived app/Environment project path. It must not execute a caller-supplied command.
- Keep `cdo-deploy` out of the `docker` group. Sudo remains limited to the two root-owned entrypoints from spec 04; do not add a general shell, Docker command or additional sudo entrypoint.
- Acquire a root-controlled `flock` keyed by app and Environment before changing that app's state. Different apps may deploy concurrently. Route changes and certificate renewal use the one proxy-wide lock defined by spec 07; do not create a competing proxy lock.
- Include the source run ID/attempt and central run identity in sanitized host audit events so the SSH session, sudo execution and deployment record can be correlated. Do not put runtime values or secrets in command arguments or audit output.

### Release preparation and transaction state

- Derive the Compose project name as `centraldevops-<app-slug>-<environment-path>` and the release directory as `/opt/apps/<app-slug>/<environment-path>/`; do not accept either from the request.
- Use the authorized, validated Compose configuration and runtime-key set from spec 10. Pull and run only the exact `ghcr.io/...@sha256:...` image reference. Never substitute a tag or print the rendered environment file.
- Before changing the current release, preserve its `compose.env`, `compose.yml` and image reference under `previous/`. Keep host runtime files restricted; runner-side decrypted bundle contents stay in a `umask 077` temporary directory, are masked and removed after the run, and are never uploaded.
- When shared database provisioning is enabled, call spec 08's root-owned database module with the registry-owned identity and validated runtime password. The deployment path must not issue its own SQL or bypass the module's validation and least-privilege rules.
- If the app declares `release_command`, run it once in a one-off container with the new image before replacing the running containers. Do not retry it automatically. If it fails, do not replace the current containers or change the route; if the database password was rotated, restore its previous value before restoring the previous app environment.
- Application migrations remain app-owned and must be backward-compatible. Restoring a previous container or password does not undo a database schema change.

### Health check and rollback

- Apply the new Compose release only after validation, previous-state capture and any required database provisioning/release command have succeeded.
- Wait for the routed service's container health check using `DEPLOY_HEALTHCHECK_TIMEOUT` from the selected Environment (default `90` seconds). Report the requested and running image digest without exposing environment contents. Keep the typical deployment within the parent PRD's five-minute target, excluding approval wait.
- If the new container does not become healthy before the timeout, fail the deployment and restore the previous database password first when it changed, then restore the previous `compose.env`, `compose.yml` and image and bring the previous release back. Do not call the route entrypoint on this path.
- If this is the first deployment and there is no previous release, stop the failed app and leave it stopped. Do not fabricate a previous digest or report a rollback as successful.
- Surface rollback failures explicitly. Preserve the previous-state snapshot and write a failed result; never convert a failed rollback into a success-shaped deployment result.

### Route activation and HTTPS smoke test

- After internal container health passes, call the idempotent `centraldevops-route apply` interface from spec 07. Let that script own route validation, Nginx edits, proxy locking and route-file rollback. An unchanged route must not be rewritten or reloaded.
- Run the HTTPS smoke test from the central runner against the validated app domain. Record its result in the central run summary and deployment result.
- Call `centraldevops-route confirm` only after the smoke test succeeds. A smoke-test failure fails the run and leaves the route/app as activated; it does not trigger automatic rollback. Do not confirm a new or changed route after a failed smoke test. Operators may diagnose the failure and manually redeploy the previous known-good digest.
- A route-plan or Nginx validation failure follows spec 07's fail-closed route rollback behavior. This is separate from the Q8 decision for an external smoke-test failure.

### Deployment records and run summaries

- Store one root-owned record per source app run and attempt at `/var/lib/centraldevops/deployments/<app>/<environment-path>/<source-run-id>-<attempt>.json`. The record is not writable by `cdo-deploy`; write it atomically and never overwrite a record for a different attempt.
- Include app, Environment, `image_ref`, `previous_image_ref` (null on first deployment), source commit, source run ID and attempt, central run URL, UTC timestamp, final result and a sanitized failure phase where applicable. Do not include runtime values, decrypted bundle data, credentials or private host details.
- Create the host record before host mutation with a non-success result. Mark it successful only after the route smoke test and any required route confirmation succeed. A failed stage, failed smoke test or interrupted central run must leave a failed/non-success record rather than a false success. The restricted entrypoint may expose a constrained finalization operation for the matching attempt; it must not allow arbitrary record edits.
- Pre-authorization rejections and local preflight failures that never connect to a host remain visible in the central Actions run and must not bypass authorization to write a host record. Every authorized attempt that invokes the host entrypoint gets a host record.
- Write the same sanitized DEP-14 fields to the central Actions run summary. Publish a machine-readable `deployment-summary.json` handoff containing only those fields and the final result so spec 12 can create a matching app-run summary. The artifact contains no `.env`, manifest secrets, sealed/decrypted bundle, private host details or process output containing secret values.
- The app-side polling action continues to match the central run by the verified source run ID/attempt. Its current draft's four-field app summary is insufficient for DEP-15; before implementation, update its consumer to read the sanitized handoff and render the DEP-14 metadata fields without runtime contents.
- Keep the record path within spec 13's backup scope. Spec 13 must prove that a deployment record is included in an off-host backup and restored during its drill.

### Runbook and acceptance boundary

- Document the normal Staging/Production deployment flow, the Production approval wait, health-check rollback, first-deployment failure, release-command failure, route errors, the no-auto-rollback Q8 smoke-test behavior, manual redeploy by previous digest, log locations and cause recording.
- Prove the deployment on Staging with a disposable test app/controlled domain before any Production rollout. Exercise health failure, first-deploy failure, release-command failure, smoke-test failure, secret redaction, record correlation and concurrent requests.
- The Staging acceptance task verifies the record exists and is secret-free. Off-host record restoration is handed to spec 13; do not claim that part of DEP-14 is complete before its restore drill.

## Deliverables

```text
.github/workflows/deploy-app.yml                  # extend with the privileged deploy stage
deployment/scripts/centraldevops-deploy           # replace spec 04's fail-closed stub
deployment/scripts/centraldevops-route             # consume spec 07's interface; do not duplicate it
deployment/scripts/lib/centraldevops_database.py   # consume the spec 08 provisioner
deployment/tools/tests/                            # focused transaction, rollback and redaction tests
docs/runbooks/deploy-and-rollback.md
docs/specs/01_init-cicd_291026/11_deploy-execution-and-rollback/
```

The app-side `request-deploy` action and its caller summary are delivered by spec 12. Off-host backup and restore of the record are delivered by spec 13.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Bind the privileged job to the Environment output from spec 10 and wait for Production approval only after request verification. | Bind directly to the dispatch input or verify the source token after approval | The approval must apply to the authorized host, and the source identity token may expire while waiting. | Yes |
| D2 | Use per-app/Environment workflow groups as scheduling, plus root-side `flock` for host correctness and spec 07's shared proxy lock for route changes. | One global workflow group or GitHub concurrency alone | A global group can cancel another app's pending deployment; GitHub concurrency is not the host correctness lock. | Yes |
| D3 | Automatically roll back only on container health-check failure; an HTTPS smoke-test failure fails the run without automatic app/route rollback. | Roll back on every failed step | Spec 07 resolved parent PRD Q8; changing this behavior would require revisiting that decision. | Yes |
| D4 | Preserve the previous runtime files and digest, and restore a rotated database password before restoring the previous app environment. | Restore the app first or attempt database schema rollback | The previous app must retain working credentials; CentralDevOps does not own application schema migrations. | Yes |
| D5 | Treat a host record as failed until the entire deployment, including runner-side smoke test and route confirmation, is finalized successfully. | Record host-side health as overall deployment success | A failure or interruption after route activation must not leave a success-shaped record. | Yes |
| D6 | Publish a separate secret-free `deployment-summary.json` handoff for spec 12. | Expose runtime bundle data or make the app workflow infer a result from logs | The app run needs the same sanitized DEP-14 fields without access to runtime environment contents. | Yes |
| D7 | Store records under `/var/lib/centraldevops/deployments/` and hand this location to spec 13. | Keep records only in GitHub Actions history | A rebuilt host must be recoverable from the off-host deployment record. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| No Environment secret or host connection is used before request authorization and required Production approval. | Inspect the workflow dependency graph and verify a Production run remains at the Environment gate before any secret-bearing step. |
| The deployment uses only the authorized Environment, host and digest. | Force mismatched inputs and confirm rejection before SSH; inspect the Compose image digest on the disposable host. |
| The deploy identity is not Docker-equivalent. | Check group membership, socket access and the exact sudo allow-list from spec 04. |
| Same-app host mutations are serialized and proxy edits/reloads share one lock. | Run concurrent requests for the same app and for different apps; inspect lock events and Nginx reloads. |
| A failed health check restores the previous release and does not change the route. | Force an unhealthy image on Staging and compare the prior digest, runtime files and route fingerprint. |
| A failed first deployment leaves the app stopped. | Force the first-release health check to fail on a disposable host. |
| A failed HTTPS smoke test fails the run without automatic rollback or route confirmation. | Inject a controlled smoke-test failure and verify the Q8 outcome and summary. |
| The deployment record and summaries contain no secrets or runtime environment contents. | Canary-scan workflow logs, the summary artifact, host records and test artifacts. |
| Host audit records, central summary and deployment record identify the same source app run. | Compare sanitized source run ID/attempt and central run URL in all three locations. |
| Deployment records are recoverable independently of the VPS. | Verify spec 13's backup/restore drill after spec 13 is implemented. |

## Out of scope

- Request authentication, OIDC verification, replay protection, registry ownership, manifest schema and Compose policy (specs 06 and 10).
- App build, provenance and caller-side deployment request/sealing/summary rendering (specs 09 and 12).
- Nginx/Certbot implementation, registry route policy and proxy lock implementation (spec 07).
- PostgreSQL installation/provisioning implementation or automatic schema-migration rollback (spec 08 and app-owned migration policy).
- Off-host backup configuration and restore-drill implementation (spec 13).
- Blue/green deployment, zero-downtime rollout, automatic DNS changes or public app ports.
