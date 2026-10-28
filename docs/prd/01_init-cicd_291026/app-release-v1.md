# Module PRD: Application Build and Deployment Request (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `REL` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

What every app repository does: build an image and record its immutable identity, then request a deployment. The privileged deployment itself is in `central-deployment-v1.md`; the shared request logic is owned by CentralDevOps.

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| REL-01 | Every app repository has exactly two manual workflows, build and deploy. They are separate operations. | Both exist in each onboarded app and neither starts the other automatically. | §1 #1, §5.2 |
| REL-02 | The build operation lets the operator choose a `source_ref`, checks out exactly that ref, runs tests, builds the image and pushes it to GHCR. | The pushed image corresponds to the chosen ref's commit. A failing test prevents the push. | §7.1 |
| REL-03 | The build records the image's immutable digest as `ghcr.io/OWNER/IMAGE@sha256:<64 hex>` in the run summary and in a metadata artifact, and also applies an explicit `sha-<full-commit>` tag as a convenience. The artifact contains metadata only. | The run summary shows a complete digest reference. The tag is never accepted as a deploy input. | §1 #2, §7.1 |
| REL-04 | The build creates a provenance attestation that links the digest to the repository, workflow and commit, and links the image package to its repository. | Attestation verification succeeds for a built digest. | §7.1 |
| REL-05 | The deploy operation takes exactly two inputs: `target_environment` (`Staging` or `Production`) and `image_ref` (a full digest reference). It rejects a malformed `image_ref` before anything is sent. | A tag reference such as `:latest` or `:sha-…` and a malformed digest are each rejected before dispatch. | §7.2 |
| REL-06 | The deploy operation runs with minimum permissions and reads the app's runtime secrets and variables from the app Environment matching `target_environment` to render the runtime environment file. | Only the permissions required for reading the repository and requesting an identity token are granted. | §7.2 |
| REL-07 | The deploy operation seals the runtime environment file, the Compose file and the environment's route manifest into one encrypted bundle that only the CentralDevOps deployment job for that Environment can open. | The bundle cannot be opened with another Environment's key. The dispatch payload contains no plaintext secret. | §1 #5, §7.2 |
| REL-08 | The request carries an identity proof from the app's own run whose audience is bound to the target Environment, the `image_ref` and the sealed bundle. | Changing any one of those three after the proof is created causes the central side to reject the request (verified in `central-deployment-v1.md`). | §1 #4, §7.2 |
| REL-09 | The request is dispatched with the dispatch-only GitHub App token. The app name is never an input; the central side derives it from the identity proof. | The dispatch step uses only the App token. No app-name parameter exists. | §7.2 |
| REL-10 | The app's deploy run waits for the central deployment, fails when it fails, and shows the central run URL in its summary. | A forced central failure makes the app run fail. The central run URL is in the summary of a successful run. | §7.2 #6, §13.4 |
| REL-11 | The shared `request-deploy` action in CentralDevOps performs sealing, identity token request, dispatch and polling. Apps reuse it rather than re-implementing it. | App deploy workflows contain no copy of that logic and reference the action by pinned SHA. | §5.1, §7.2, §12.2 |
| REL-12 | A request that exceeds the dispatch payload limit (about 65 KB including the encoded bundle) is detected and rejected early with an explanatory message. | An oversized test bundle fails before dispatch with a message naming the limit. | §7.2 #5 |
| REL-13 | Rollback is performed by running the deploy operation again with the previous known-good digest. | A Staging rollback to the previous digest succeeds using only the deploy operation. | §8.4, §15.6 |
| REL-14 | The operator flow is documented: run build, copy `image_ref` from the build summary, run deploy for `Staging`, verify, then run deploy for `Production`. | The documented flow is followed in the first Staging-to-Production release of an app. | §15.3 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| REL-15 | The build for a Staging-only image may skip the attestation, but any digest intended for Production has one. | A Production deployment of an unattested digest is rejected (see `central-deployment-v1.md`). | §7.1, §17 #5 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| REL-16 | A starter template provides the two app workflows, the route manifest and the Compose skeleton for a new app. | A new app is onboarded from the template with no edits to the workflow logic. | §15.2 |
