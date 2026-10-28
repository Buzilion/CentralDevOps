# Module PRD: Central Deployment (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `DEP` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

The privileged deployment that runs inside CentralDevOps after an app requests it: authenticating the request, deciding where it may go, deploying by digest, handling failure, and recording the result. App-side request creation is in `app-release-v1.md`; manifest and Compose policy rules are in `registry-and-policy-v1.md`; route activation is in `routing-and-tls-v1.md`.

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| DEP-01 | The privileged deployment runs in the CentralDevOps repository and is triggered by an authenticated cross-repository dispatch. It is not a reusable workflow running in the app's context. | No deploy credential exists in any app repository. An app-context workflow cannot reach any VPS. | §1 #3, §8 |
| DEP-02 | Authorization is a separate stage that runs before any Environment or secret is used. It verifies, for every request: the identity token's signature, issuer and expiry; that the token audience equals the recomputed binding of Environment, `image_ref` and bundle; that the token's repository maps to an app in the registry (the app is derived, never supplied); that the workflow is that repository's `deploy.yml` on an allowed ref; that the ref is in the registry's allowed refs; and that the Environment claim equals `target_environment`. | A negative test per check is rejected before the deploy stage starts: wrong repository, wrong workflow file, disallowed branch, mismatched Environment, tampered `image_ref`, tampered bundle, expired token. | §8.1, §8.2 |
| DEP-03 | Each request is single-use, identified by the source `run_id` and `run_attempt`. A replay is rejected. | Re-sending a previously successful request is rejected. | §8.1, §12.3 |
| DEP-04 | The `image_ref` must be `ghcr.io/<registry image repository>@sha256:<64 hex>` for the app identified in DEP-02. | Another app's image, a tag reference and a malformed digest are each rejected. | §8.1 |
| DEP-05 | When the registry requires attestation (always for Production), the provenance is verified against the app repository and workflow, and the deployment fails if verification fails. | A Production deployment of a digest without valid provenance fails. | §7.1, §8.1, §17 #5 |
| DEP-06 | The selected Environment and the target host cannot disagree. The registry file for the app and Environment must declare the same Environment, the inventory is derived from `target_environment`, and every resolved host must exist in that inventory. Any mismatch fails before the deploy stage. | A forced mismatch fails before the deploy stage, so a Production approval always applies to the host actually targeted. | §8.1, §8.2 |
| DEP-07 | Each placement group resolves to exactly one host. Any other result fails the deployment. | Zero or multiple hosts in a placement group fail the run. | §8.3 #5 |
| DEP-08 | A Staging deployment runs without manual approval. A Production deployment's privileged stage waits for approval in the CentralDevOps `Production` Environment. Request verification happens before the approval wait, so a late approval still works. | A Production request approved after its identity token has expired still deploys. | §8.2 |
| DEP-09 | Concurrency is enforced on the server. Two deployments of the same app and Environment never run at once, and two apps never edit or reload the proxy at the same time. A pending deployment of one app is never silently cancelled by another app's deployment. | Two simultaneous deployments of the same app are serialised or one fails cleanly. Two different apps deploy concurrently without simultaneous proxy edits. | §8.2, §8.4 |
| DEP-10 | The deployment validates the manifest and the Compose policy (`registry-and-policy-v1.md`), checks that the runtime environment contains exactly the keys the manifest declares and none that are reserved, and only then connects to the host. | A missing, extra or reserved key fails the deployment before any change on the host. | §8.3 #3–6 |
| DEP-11 | The deployment connects with the restricted deploy identity, pulls the exact digest, renders the runtime configuration, replaces the running containers and waits for the container health check within a configurable timeout (default 90 s). | The running container's image digest equals the requested digest. A health check failure fails the deployment. | §8.3 #7–8, §4.3 |
| DEP-12 | If the health check fails after a replacement, the previous release is restored and the route is not changed. A failed first deployment is left stopped. | A forced unhealthy image leaves the previous release serving and the route configuration unchanged. | §8.4 |
| DEP-13 | Decrypted bundle contents exist only in a restricted temporary location, are masked in logs, are never uploaded as artifacts and are removed after the run. | A canary-secret test (SEC-12) finds no canary value in logs or artifacts. | §8.3 #2, §12.3 |
| DEP-14 | Every deployment, successful or failed, writes a deployment record containing app, Environment, `image_ref`, previous `image_ref`, git commit, source run, central run URL, UTC time and result. The record contains no secrets, is stored on the host and is included in the off-host backups. | A record with all fields exists after each Staging deployment and is restored during the restore drill. | §13.4 |
| DEP-15 | Each deployment produces a run summary in the central run and in the app run. Runtime environment contents are never printed. | Summary contains the fields above and no secret value. | §8.3 #10 |
| DEP-16 | The deployment workflow only accepts dispatches that run the reviewed `main` branch of CentralDevOps. | A dispatch referencing another branch is rejected. | §8.3 #1 |
| DEP-17 | Every deployment is attributable end to end: the deploy account's SSH sessions and sudo executions are logged, and the deployment record links the central run to the source app run. | For a test deployment, the host log and the record identify the same app run. | §8.5 |
| DEP-18 | A runbook describes what to do when a rollout fails: route unchanged, read central and app run logs plus centralised container logs, rerun with the previous digest if needed, record the cause. | Runbook exists and is used in a Staging failure exercise. | §15.6 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| DEP-19 | An optional manifest `release_command` runs once in a one-off container using the new image before the replacement; a failure aborts the deployment and leaves the running release untouched. | A failing release command aborts the deployment and the previous release keeps serving. | §11.3 |
| DEP-20 | A throwaway-app acceptance test proves the dispatch path, the identity-token audience and claims, and the selection of the matching CentralDevOps Environment, before the full pipeline is built. | A recorded passing run with correct `repository`, `job_workflow_ref` and `environment` claims. | §16 step 2, §17 #1 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| DEP-21 | Deployment status is mirrored to GitHub Deployments. | Deployment status for an app shows in the app's Deployments view. | §13.4, §17 #12 (deferred) |
