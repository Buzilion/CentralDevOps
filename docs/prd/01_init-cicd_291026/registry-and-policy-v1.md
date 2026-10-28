# Module PRD: App Registry, Manifest, Compose Policy and Onboarding (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `REG` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

The reviewed data and rules that decide where each app runs and what it may do: the central registry, the app-owned route manifest, the policy applied to the app's Compose file, the capacity control for up to 6 apps, and the steps to onboard an app. Schemas, examples and workflow skeletons are in the companion deployment contract document, which is still at v3 (see Open Questions in the parent PRD).

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| REG-01 | A central registry has one reviewed file per app and Environment. It decides: source repository, image repository, allowed refs, whether attestation is required, allowed domains, placement groups, upstream mode and host port, resource limits, and database settings. | A registry file with a missing or invalid field fails schema validation in CI. | §1 #6, §9.1, §9.2 |
| REG-02 | The app manifest, in the app repository, may request only: its domain, container port, service name, health path, TLS preference, required runtime keys and an optional release command. It cannot set placement, limits, allowed refs or image repository. | A manifest containing a registry-owned field fails validation. | §9.1 |
| REG-03 | The domain requested by a manifest must be in the registry's allow-list for that app and Environment. No two registry entries claim the same domain. | A manifest requesting another app's domain, or an unlisted domain, is rejected. A registry change duplicating a domain fails CI. | §9.1 |
| REG-04 | Registry and manifest are validated against schemas in CI and at deployment time. | Invalid files fail the pull request and the deployment. | §5.1, §8.3 #3 |
| REG-05 | The Compose policy is evaluated on the fully rendered Compose configuration, not on the source file. It rejects: privileged mode, added capabilities, device access, host PID, IPC or network mode, user-namespace changes and security options that weaken confinement; bind mounts outside `/opt/apps/<app>/<env>/` and any mount of the Docker socket; published ports; networks other than the app's own default, `edge` and `db`; an app service image that is not the requested digest, or other images that are not digest- or version-pinned; a routed service without a health check; missing or over-ceiling memory and CPU limits; any `env_file` other than `.env`. | For each rule, a failing fixture is rejected and a compliant baseline passes. A violation introduced through variable interpolation or an override file is also rejected. | §9.4 |
| REG-06 | Every app has memory and CPU ceilings in the registry, and the policy rejects a Compose file missing limits or exceeding the ceilings. | A Compose file without limits, or above the ceilings, fails the deployment. | §2, §9.4 |
| REG-07 | A capacity check in CI sums the memory limits of all registry entries per placement host and fails the pull request if the sum exceeds the host's budget declared in inventory. It runs before a second app is onboarded. | Adding an entry that exceeds the budget fails the PR. Every host used by a registry entry has a declared budget. | §9.3 |
| REG-08 | Host ports for private-IP routing are allocated centrally and are unique per host. | A registry change duplicating a port on the same host fails CI. | §9.2 |
| REG-09 | An app is onboarded without changing CentralDevOps workflows: (1) a pull request adds the app's `staging.yml` and `production.yml` registry files and passes the capacity check; (2) DNS records are created; (3) the app repository gets its workflows, Compose file, manifests, two Environments, runtime secrets and dispatch App credentials; (4) build, deploy to Staging, verify, then deploy to Production. | The second app is onboarded by following the steps with no workflow edits in CentralDevOps. | §15.2 |
| REG-10 | The app contract is documented for developers: Dockerfile, `compose.yml`, per-environment manifest, a health endpoint, stateless containers with durable data in volumes, the database or object storage (not the writable layer), runtime configuration only via environment variables, and no secrets in image layers, build arguments, labels or committed Compose files. | The onboarding documentation contains the contract. | §12.1, §13.2 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| REG-11 | Containers run as non-root where the app allows it. | Onboarding checklist records the user for each app. | §12.3 |
| REG-12 | Sizing is reviewed when the fourth app is onboarded. | A recorded review exists at four apps. | §2 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| REG-13 | Placement for an app can be a set of hosts instead of exactly one, with a load balancer and rolling deployment. | An app runs on two hosts behind a balancer without workflow rewrites. | §14.2 #4 |
