# Spec 06: Registry and Compose Policy

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 06 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation blocked on completion of specs 01 and 03 |
| Depends on | `01_foundation-and-access` and `03_host-bootstrap-and-hardening` (both checklists must be complete before implementation) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRDs | `docs/prd/01_init-cicd_291026/registry-and-policy-v1.md` (`REG`), `docs/prd/01_init-cicd_291026/routing-and-tls-v1.md` (`RTE-02`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§4, 6; `docs/design/naming-and-repository-conventions.md` §§3–5, 8.2; v5 design §§9.1–9.4, 16; spec 03 capacity policy |

## What

Define the reviewed registry and app-owned manifest schemas, enforce cross-file ownership and capacity rules, and implement the central Compose policy against the fully rendered configuration. This spec delivers the validators, an app-CI manifest entry point and the CI gate that later deployment workflows consume. It does not configure a host or deploy an app.

## Context

- Do not implement this spec until specs 01 and 03 are complete. Spec 01 supplies protected changes and CI conventions; spec 03 supplies the environment inventories and host capacity facts this spec must resolve.
- Registry and manifest values control placement, domains, images and runtime policy. The manifest and Compose file are app-owned inputs, so validation must fail closed before any host state changes.
- The v5 design and the current module PRDs are authoritative. The v3 deployment contract is useful as an example, but it is not the schema specification: in particular, the manifest must not gain extra fields such as an app identity, `edge_alias`, `routing.enabled` or a per-app health timeout.
- Spec 03 sets initial planning budgets of 2560 MiB for Production and 1024 MiB for Staging, subject to measurement. The validator reads the reviewed inventory values; it must not hard-code those budgets.
- Spec 03 Task 2 names the reserve fact `platform_reserve_mib`, while its host-budget invariant uses `reserve_mib` as shorthand. Use `platform_reserve_mib` as the inventory key and ensure spec 03 is consistent before its checklist is considered complete.
- There are no approved app registry entries in this spec. Do not create real app records from illustrative names, domains, host aliases, ports or repositories in the design examples.
- `private_ip` is part of the routing data contract and must be accepted by the registry schema. This does not enable private-IP deployment in v1; app-authored published ports remain forbidden.

## Requirements

| ID | Statement | Source |
|---|---|---|
| P-01 | Every registry entry at `apps/<app>/staging.yml` or `apps/<app>/production.yml` validates against a strict schema. Missing, invalid, unknown or misplaced fields fail. | REG-01 |
| P-02 | The app-owned manifest can request only its service name, container port, domain, health path, TLS preference, required runtime-key names and optional release command. Registry-owned fields and unknown properties fail validation. | REG-02 |
| P-03 | A manifest domain must be allow-listed for that app and Environment. No two registry entries claim the same domain, including across Environments. | REG-03 |
| P-04 | Registry and manifest schema validation is available to CI and deployment preflight. Central registry changes and app manifest changes fail their respective pull-request checks; deployment preflight repeats validation before host changes. | REG-04 |
| P-05 | Compose policy is applied to the fully rendered configuration and rejects the prohibited privilege, mount, network, image, health-check, resource-limit and `env_file` settings in REG-05. Interpolation and explicit override files cannot bypass a rule. | REG-05 |
| P-06 | Registry entries declare CPU and memory ceilings. Every rendered service has CPU and memory limits, and the sum of service limits cannot exceed the app's registry ceilings. | REG-06 |
| P-07 | CI sums each registry entry's memory limit by resolved app host and rejects a total above that host's inventory `capacity_budget_mib`. Every used host must have a valid budget. | REG-07 |
| P-08 | The registry schema accepts `docker_edge` and `private_ip`. Private-IP host ports are centrally allocated, within the reserved range, and unique per resolved app host. | REG-08, RTE-02 |

## Design

### Registry schema

Create `deployment/schemas/registry.schema.json` using JSON Schema Draft 2020-12. Reject unknown properties at every object level. A registry entry follows this shape:

```yaml
app: customer-builder
environment: staging
repository: example-org/customer-builder
image: ghcr.io/example-org/customer-builder
allowed_refs:
  - refs/heads/main
require_attestation: false
domains:
  - builder-staging.example.com
placement:
  app_group: app_nodes
  proxy_group: proxy_nodes
  database_group: database_nodes
routing:
  upstream_mode: docker_edge
  host_port: 21001
limits:
  memory: 512m
  cpus: "0.50"
database:
  enabled: true
  name: customer_builder_stg
  user: customer_builder_stg
```

Schema and semantic rules:

- `app` is a lowercase kebab-case slug; `environment` is exactly `staging` or `production` and must match the path.
- `repository` and `image` are reviewed source-repository and GHCR repository identities, not request-supplied identities or image tags. The image is a repository name; the requested deployment digest is checked separately.
- `allowed_refs` and `domains` are non-empty, unique lists. Domains are lowercase FQDNs without wildcards. Production entries require `require_attestation: true`.
- `placement.app_group` and `placement.proxy_group` are required. `database_group` is required when `database.enabled` is true. Every referenced group must resolve in the matching Environment inventory.
- `routing.upstream_mode` is exactly `docker_edge` or `private_ip`. `host_port` is required for `private_ip`; when present it is an integer from 21000 through 29999. The registry validator checks uniqueness only for private-IP ports, on the resolved app host.
- `limits.memory` uses an explicitly supported Compose memory-unit format; `limits.cpus` is a positive decimal value. The validator converts memory values to bytes without floating-point rounding before comparing budgets.
- `database.enabled` is required. `name` and `user` are required when it is true and must be valid PostgreSQL identifiers.

The v5 design example includes `host_port` on a `docker_edge` entry. The schema may retain that optional field for forward compatibility, but no port is reserved or published for `docker_edge`.

### App manifest schema

Create `deployment/schemas/app-manifest.schema.json`, also using Draft 2020-12 and `additionalProperties: false` at every object level. Preserve the v3 document's useful nesting while limiting fields to REG-02:

```yaml
app:
  service: app
  container_port: 3000
routing:
  domain: builder-staging.example.com
  tls: true
health:
  path: /health
runtime_env:
  required:
    - APP_AUTH_SECRET
    - DB_PASSWORD
release_command: null
```

`release_command` may be omitted, `null`, or a non-empty argument array; it is never a shell command string. `runtime_env.required` contains unique key names only, never values. The manifest has no app identity, image repository, allowed refs, placement, limits, database settings, `edge_alias`, routing enable switch or timeout. Central code derives identity and platform-owned values.

### Registry integrity and inventory resolution

`deployment/tools/validate-registry.py` is the shared fail-closed validator:

- `--all` validates every registry file and global invariant for CI.
- `--manifest-only` validates one app-owned manifest without requiring access to the CentralDevOps registry; app CI can run this mode on pull requests.
- Deployment mode validates the selected registry entry and supplied app manifest against the verified app and Environment. The requested `image_ref` must be exactly `<registry.image>@sha256:<64 lowercase hex characters>`; the app name is derived by the caller from verified identity, never accepted as an untrusted workflow input.
- An absent `apps/` directory or an empty registry is valid until an app is onboarded. Any discovered malformed or unsupported registry file fails; it is never silently skipped.
- Registry path, `app`, and `environment` must agree. Each referenced group resolves to exactly one host in its matching Environment inventory for this v1 topology. A group in the other Environment cannot satisfy the lookup.
- Domain claims are unique across all registry entries. The manifest's requested domain must be in its matching registry entry.
- For `private_ip`, `host_port` claims are unique per resolved app host and Environment. Reuse on another host is allowed.
- Allowed-ref and provenance authorization remain the responsibility of the deployment authorization stage in spec 10.
- Inventory resolution uses the pinned `ansible-inventory` tool from spec 03 rather than a second, incomplete Ansible YAML parser. Every app host used by a registry entry must declare `physical_memory_mib`, `platform_reserve_mib` and `capacity_budget_mib`; the budget must be positive and no greater than physical memory minus reserve.
- The validator's deployment mode is a preflight interface for specs 10 and 12. Those specs must call it before deployment or bundle submission. Until private-IP deployment is implemented and accepted by a later spec, deployment mode rejects a `private_ip` entry with an explicit unsupported-mode error; it never silently treats it as `docker_edge`.

Use pinned Python dependencies for YAML loading and JSON Schema validation. The same validator version and schema files are used by CI and deployment preflight. Errors identify the file, field and rule without echoing runtime values.

### Capacity control

For each registered app, resolve `placement.app_group` to its single app host, normalize `limits.memory` to bytes, and sum those limits by `(Environment, host alias)`. Convert the host's `capacity_budget_mib` to bytes and fail when the sum exceeds it. Also fail on a missing or invalid host budget, a group that resolves to zero or multiple hosts, or a budget greater than `physical_memory_mib - platform_reserve_mib`. Do not substitute reference VPS sizes or a default budget.

The capacity check is memory-based as required by REG-07. CPU ceilings are enforced per app by Compose policy; this spec does not invent an aggregate host CPU budget.

### Compose rendering and policy

Create `deployment/scripts/centraldevops-compose-policy`. It validates the app manifest and registry context, then evaluates the JSON produced by Docker Compose v2 `config --format json`, never the source YAML alone. The caller supplies the requested digest and all Compose files that will actually be used. Derive the project name and project directory from the authorized app and Environment using `docs/design/naming-and-repository-conventions.md` §5.2. Pass files explicitly; disable implicit override discovery and clear ambient `COMPOSE_*` variables so unreviewed runner state cannot affect the result.

Render using a trusted interpolation environment containing only platform-derived values such as the requested digest. Runtime values are not printed. Capture the rendered JSON and report only sanitized rule IDs, service names and field paths; never print the JSON or secret-bearing Compose diagnostics.

Reject the following in the rendered configuration:

| Rule | Enforcement |
|---|---|
| Privileged execution and confinement weakening | Reject `privileged: true`, any `cap_add` or device access, `pid`, `ipc` or `network_mode` set to `host`, any `userns_mode`, and `security_opt` values that weaken confinement. Permit only the recognized strengthening option `no-new-privileges:true`; unknown options fail closed. |
| Host filesystem and Docker access | Every bind source resolves under `/opt/apps/<app>/<environment>/`. Reject a Docker socket mount by source or target, including normalized `/run/docker.sock` and `/var/run/docker.sock` paths. |
| Published ports | Reject every app-supplied `ports` entry. The v1 `docker_edge` path publishes no app ports. Accepting `private_ip` in the schema does not authorize or implement a central-generated port binding. |
| Network access | Permit only the project default network, external `edge`, and external `db` when the registry enables the database. For `docker_edge`, the routed service must join `edge`. The shared networks must use their exact names and cannot be redefined. |
| Image identity | The routed service named by the manifest must use exactly `<registry.image>@sha256:<64 lowercase hex characters>` for the requested digest. Every other service image must be digest-pinned or carry an explicit fixed version tag; floating tags are rejected. Reject `build` in deployment Compose. |
| Health | The routed service exists and has an enabled, non-empty Compose health check. |
| CPU and memory | Every service has both `cpus` and `mem_limit`. Sum the rendered limits across all services and reject totals above the registry's CPU or memory ceiling. Reject conflicting or unsupported duplicate limit declarations. |
| Runtime files | A service may use no `env_file` or only the app runtime file `.env`, resolved under the app's project directory. |
| Named volumes | Require project-scoped volumes. Reject external volumes and explicit names that do not use the exact derived project-name prefix. |
| Project identity | If Compose declares a top-level `name`, it must match the derived stable project name. |

The policy accepts the project's default network and project-scoped volumes. It does not allow an app to create another network or to mount files outside its Environment directory. A central-generated private-IP publish path, if introduced later, must be separately authenticated and explicitly added to this policy; it is not part of this spec.

The deployment bundle contains only declared Compose inputs. Tests must also pass an explicit override file to the renderer and prove that an override cannot hide a prohibited final setting. Interpolation and override merging must be evaluated before policy checks.

### CI and downstream call contract

- Extend the existing `.github/workflows/lint.yml` with a read-only `registry-policy` job on pull requests and pushes to `main`. It validates schemas, registry/inventory integrity, capacity, Compose fixtures and tool tests. It needs no GitHub secrets and makes no host connection.
- Add the exact `registry-policy` status context to `.github/rulesets/main.json` and the apply/audit procedure in `docs/runbooks/github-environments.md`; a failing validator must block merge.
- The CI job passes when there are no production registry entries, but always runs schema and validator fixtures.
- App pull-request CI invokes `validate-registry.py --manifest-only` using a pinned CentralDevOps revision; deployment preflight validates the manifest again against the selected registry entry.
- The composite action at `.github/actions/validate-app-manifest` accepts one `manifest-path` relative to `GITHUB_WORKSPACE`, rejects paths that resolve outside the workspace, calls the same pinned `--manifest-only` validator, and needs no secrets or registry access. Callers pin it to a reviewed 40-character commit SHA and pass the path through an environment variable, not direct shell interpolation.
- Document local commands and rule meanings in `docs/runbooks/registry-and-compose-policy.md`. The later deploy workflow (spec 10) and app request flow (spec 12) must invoke the validators before host changes or dispatch. This spec supplies those call interfaces but does not implement those workflows.

### Deliverables

```text
deployment/schemas/registry.schema.json
deployment/schemas/app-manifest.schema.json
deployment/tools/requirements.txt
deployment/tools/validate-registry.py
deployment/tools/tests/
deployment/tools/tests/fixtures/
deployment/scripts/centraldevops-compose-policy
.github/actions/validate-app-manifest/action.yml # app pull-request CI entry point
.github/workflows/lint.yml                 # add registry-policy job
.github/rulesets/main.json                 # require registry-policy
docs/runbooks/github-environments.md       # update required-check audit
docs/runbooks/registry-and-compose-policy.md
```

Do not add real `apps/<app>/<environment>.yml` files, app manifests, a Docker role, deployment workflow, proxy configuration or live host changes in this spec.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Current v1 PRDs, `docs/design/` and v5 design govern; v3 companion examples are illustrative when their fields or behavior conflict. | Copy v3 contract verbatim | The PRDs and current design explicitly narrow manifest authority and define the current inventory budget names. | Yes |
| D2 | The manifest schema contains only the REG-02 request fields, using the existing nested `app`, `routing`, `health` and `runtime_env` shape. | Keep every v3 manifest field | The allowlist must not let an app choose identity, alias, timeout or other platform-owned values. | Yes |
| D3 | `private_ip` is schema-valid, but v1 deployment supports only `docker_edge` and rejects app-published ports. | Treat schema acceptance as deployment support | RTE-02 requires the forward-compatible schema; the current contract and REG-05 prohibit app-published ports, and RTE-13 is not delivered. | Yes |
| D4 | Each placement group resolves to exactly one host in v1; capacity and private port uniqueness use the resolved app host. | Allocate one registry entry across a host set | Multi-host placement is REG-13 and is not part of this release. | Yes |
| D5 | Inventory `capacity_budget_mib` is authoritative; memory values are normalized to bytes for comparisons. | Recompute a budget from nominal VPS size or hard-code examples | Host capacity must reflect the measured platform reserve recorded by spec 03. | Yes |
| D6 | The CI status is named `registry-policy` and is required by the existing `main` ruleset. | Run validation in an optional job | An optional failing check does not enforce REG-01, REG-04 or REG-07 before merge. | Yes |
| D7 | No real app registry record is seeded by this spec. | Copy illustrative app data from a design example | No app-specific placement, domains, GHCR repository or limits have been approved here. | Yes |
| D8 | Named volumes remain scoped to the derived Compose project; external or cross-project volume names are rejected. | Allow app-selected shared volumes | An app must not gain access to another app's persistent data through a shared Docker volume. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| Unknown registry or manifest fields never pass. | Negative schema fixtures for unknown top-level and nested properties. |
| A manifest cannot choose registry-owned identity or policy. | Negative fixtures for image, placement, allowed refs, limits and database fields. |
| Registry domains are globally unique and manifests request only an allocated domain. | Duplicate-domain and non-allow-listed-manifest tests. |
| `private_ip` is schema-valid but cannot cause a v1 deployment or app-authored port publication. | Schema fixture passes; deployment-mode fixture and Compose `ports` fixture fail clearly. |
| Capacity never exceeds the budget of the resolved host. | Inventory fixture tests at the exact limit and one byte over; validate budget against physical memory and reserve. |
| Compose policy sees interpolation and explicit overrides before checking. | Rendered-config tests introduce prohibited values through both mechanisms and fail. |
| No runtime values are written to CI logs or summaries. | Secret-canary fixture appears in rendered input; assert it is absent from captured output. |

## Error Behavior

| Situation | Behavior |
|---|---|
| A prerequisite checklist is incomplete. | Do not implement or run this spec against a host; report the missing prerequisite. |
| A schema, path/content match, registry claim, group or budget is invalid. | Fail CI or deployment preflight with file, field and rule; do not substitute defaults or skip the record. |
| Inventory group is missing, belongs to another Environment or resolves to multiple hosts. | Fail before SSH or host changes. |
| Registry capacity exceeds the budget. | Fail the required CI check and deployment preflight; report total and budget in MiB without exposing secrets. |
| Compose cannot render, a required interpolation value is missing, or the Compose CLI is unavailable. | Fail closed. Never fall back to source-file inspection or an older parser. |
| Rendered Compose violates policy. | Fail before host changes and emit a sanitized rule ID; do not print rendered environment values or full configuration. |
| A registry entry selects `private_ip` before its deployment path is implemented. | Fail with an explicit unsupported-mode message; never silently use `docker_edge` or open a port. |
| There are no app registry entries yet. | CI succeeds only after running the schema and validator tests; the empty production registry is not an error. |

## Testing Strategy

- **Schema tests:** valid Staging and Production records; missing fields; wrong app/environment path; unknown top-level and nested fields; invalid domains, refs, image repository, limits, group names and database identifiers; `private_ip` accepted with a valid host port and rejected without one.
- **Manifest tests:** compliant baseline; every unsupported registry-owned field; unknown fields; duplicate runtime keys; invalid port/domain/health path; release command as an argument array and invalid string form.
- **Registry integrity tests:** duplicate domains across apps and Environments; duplicate private ports on one host; same port on different hosts; missing or ambiguous placement groups; manifest domain not in registry; empty registry; no cross-Environment inventory fallback.
- **Capacity tests:** multiple app limits summed on one host; separate host totals; exact-budget pass; over-budget failure; invalid or missing budget; reserve greater than physical memory; supported memory-unit normalization.
- **Compose policy tests:** a compliant rendered baseline plus a negative fixture for every rule in the policy table. Include a routed service missing `edge`, an external or cross-project named volume, values introduced through variable interpolation and an explicit override file. Test that policy output never contains a runtime canary.
- **App CI tests:** call the manifest action for both Environment manifests at a pinned CentralDevOps revision; invalid schema fixtures fail without registry credentials.
- **CI acceptance:** a clean pull request passes `registry-policy`; a deliberately invalid fixture causes the required status to fail. Confirm the ruleset audit reports this exact required check.
- **Deployment interface:** exercise the deployment-mode validator with a synthetic verified app/environment and digest, and prove malformed manifests, mismatched domains and unsupported `private_ip` fail before any host operation.

## Out of Scope

- Implementing `private_ip` publishing, firewall rules or a separate proxy host (RTE-13).
- Nginx, DNS, certificate issuance and route activation (spec 07).
- Wiring the validators into `deploy-app.yml` or specific app repository workflows (specs 10, 12 and 15); those specs must consume the interfaces delivered here.
- App onboarding instructions, app contract and capacity review at app four (REG-09 to REG-12; spec 15).
- Docker Engine installation, deploy runtime or changes to a VPS (spec 04 and later deployment specs).
- Creating actual app registry entries or approving example domains, ports, resource limits or placement.
