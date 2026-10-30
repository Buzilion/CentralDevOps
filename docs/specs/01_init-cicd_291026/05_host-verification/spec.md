# Spec 05: Host Verification

| Item | Value |
|---|---|
| Project | `01_init-cicd_291026` (spec 05 of 15; see `../00_spec-roadmap.md`) |
| Status | Draft for review; implementation is gated by completion of spec 04 |
| Depends on | `04_docker-and-deploy-runtime` (all checklist items complete and disposable-host evidence recorded) |
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module PRD | `docs/prd/01_init-cicd_291026/infrastructure-v1.md` (`INF`) |
| Design | `docs/design/infrastructure-contracts-and-invariants.md` §§3–6; `docs/design/variables-and-secrets.md` §4.1; v5 design §§4.4, 6.3–6.4, 8.5, 12.1, 13.1–13.2, 15.1, 15.4, 16 step 5 |

## What

Deliver the on-demand `verify-vps.yml` operation and its read-only Ansible checks. An operator selects `Staging` or `Production` and either one exact inventory host, one exact inventory group, or the whole selected Environment. The operation reports a sanitized `PASS` or `FAIL` for every applicable check on every selected host and exits unsuccessfully if any check fails.

This spec adds checks for the host, Docker/network, and restricted deploy-runtime roles delivered by specs 03 and 04. The check contract is role-scoped: later specs add their checks alongside each new configure role, so verification grows with the platform without passing an unconfigured role as successful. The later role specs own the Nginx/TLS, PostgreSQL, monitoring, and backup checks.

Verification diagnoses state; it never remediates it. Fix a failed check through the owning bootstrap/configure/deploy process, then run verification again.

## Context and sequencing

- Do not implement or run this spec until every task in `04_docker-and-deploy-runtime/checklist.md` is complete and the disposable-host evidence is recorded. Spec 04 itself depends on the completed bootstrap and hardening proof from spec 03.
- The workflow rejects the deployment-dispatch GitHub App identity established by spec 02. Do not guess its actor ID or substitute a placeholder. The workflow cannot be enabled for use until this identity is proven.
- Infrastructure workflows use the selected Environment's branch policy (any branch for `Staging`, `release/*` only for `Production`), use that Environment's fixed inventory, and bind the credential-using job to the same GitHub Environment. Production's configured Environment protection applies before its credentials are available, even though verification is read-only.
- Verification connects as `cdo-admin` using the selected Environment's `ANSIBLE_SSH_PRIVATE_KEY` and the committed, strict host-key pin. It does not use `DEPLOY_SSH_PRIVATE_KEY`, `GHCR_PULL_TOKEN`, backup credentials, or monitoring credentials from GitHub Actions.
- Use inventory role/group membership to decide which role checks apply to a host. Do not infer roles from hostnames or silently skip a check for a role assigned to that host.
- `INF-06` names checks owned by later role specs. At this spec's close, checks for roles not yet delivered are explicitly deferred; they become mandatory as those roles are added. Do not add placeholder roles or claim that a deferred check passed.

## Requirements

| ID | Statement | Source |
|---|---|---|
| HV-01 | Infrastructure verification is manual-only, runs from a ref allowed by its selected CentralDevOps Environment, and rejects the dispatch App actor before the Environment-bound job or any SSH connection starts. `Staging` accepts any branch; `Production` accepts only `release/*`. | INF-14; SEC-14 |
| HV-02 | The workflow accepts only `Staging` or `Production` and an optional exact host/group limit. It derives the inventory from the selected Environment. An empty limit means all hosts in that Environment; arbitrary Ansible patterns, CLI options, and cross-Environment targets are rejected before secrets or SSH are used. | INF-06, INF-08 |
| HV-03 | The credential-using job is bound to the selected GitHub Environment, requires its protections, and uses only that Environment's admin SSH key. Permissions and pinned actions follow the repository's least-privilege workflow rules. | INF-09, INF-14, INF-15; SEC-07, SEC-14 |
| HV-04 | Verification is read-only. It makes no persistent host changes, runs no configuration/remediation tasks, and does not treat Ansible check mode as proof of read-only behavior. Temporary Ansible module data is cleaned up. | INF-06 |
| HV-05 | Every applicable check produces exactly one sanitized `PASS` or `FAIL` result per host. Any failed or indeterminate check fails the overall run. A host that cannot be reached is never reported as passing; applicable checks that could not run are reported as failed/not evaluated. | INF-06 |
| HV-06 | The verifier covers access and expected users, firewall state, Docker/Compose, `edge` and `db` networks, deploy-script presence/ownership/integrity, deploy-user sudoers, and disk/inode measurements. Monitoring-connectivity and backup-age checks are added with their roles; proxy and database roles add Nginx/TLS and PostgreSQL checks. | INF-06, INF-18 |
| HV-07 | Every role in a configure profile has an integrated, read-only verification check and a test. A role assigned to a host without an integrated check is a failure, not a skip. | INF-18 |
| HV-08 | A VPS verification runbook explains target selection, safe use after bootstrap/configure, result handling, and the extension points for later role checks. | INF-17 |

## Deliverables

```text
.github/workflows/verify-vps.yml
playbooks/verify.yml
roles/<configured-role>/tasks/verify.yml
deployment/tools/                    # target validation and focused tests, reusing
                                     # spec 04's inventory resolver where practical
docs/runbooks/verify-vps.md
```

Add `tasks/verify.yml` to the configured roles from specs 03 and 04 when those implementations do not already provide the required check. Later configure-role specs add their own `tasks/verify.yml` and tests, and integrate them into `playbooks/verify.yml` in the same change.

## Design

### Workflow contract

`.github/workflows/verify-vps.yml` is `workflow_dispatch` only:

| Input | Contract |
|---|---|
| `target_environment` | Required choice; exact case-sensitive values `Staging` or `Production`. Selects the matching GitHub Environment and fixed inventory path. |
| `limit` | Optional string. Empty means every host in the selected inventory. A non-empty value must exactly match one host alias or group in that inventory. |

There is no dry-run input: verification is always read-only. Do not accept an inventory path, host address, SSH username, Ansible option, arbitrary pattern, or credential as input.

The workflow must:

1. Use a secret-free preflight job to validate that the workflow ref is allowed by the exact Environment value, reject the spec-02 dispatch App actor, and resolve the target against the fixed inventory for that Environment.
2. Reject a missing/empty inventory, a malformed or unknown target, and any target found only in the other Environment before the credential-using job starts. Reuse the inventory/target resolver established by spec 04, or extract a shared helper without changing its tested configure behavior.
3. Pass validated values through environment variables. Do not interpolate dispatch inputs into shell commands or pass unvalidated values to Ansible.
4. Bind the verification job to the selected GitHub Environment and require successful preflight. Confirm any existing `ANSIBLE_INVENTORY_PATH` Environment variable matches the trusted Environment-to-inventory mapping; never treat that variable as an operator-controlled source of truth.
5. Use `permissions: {}` by default and grant only `contents: read` where checkout is needed. Pin third-party actions to reviewed full commit SHAs and disable persisted checkout credentials.
6. Use the Environment's `ANSIBLE_SSH_PRIVATE_KEY` and strict `known_hosts` pin. Create any necessary temporary key file with restrictive permissions and remove it in unconditional cleanup. Do not pass unrelated Environment secrets to the job.
7. Invoke `playbooks/verify.yml` for the validated target, then fail the workflow if any applicable check failed or could not be evaluated.

### Read-only execution and result contract

- Run Ansible using the selected inventory and the existing strict host-key policy. A wrong or missing pin fails closed; the workflow must never scan and trust a replacement key.
- Use read-only Ansible modules and commands only. Do not call package, service, firewall, account, file-writing, Docker-network creation, or other state-changing operations. Commands must use argument arrays where possible, have `changed_when: false`, and avoid shell interpolation.
- `become` may be used for privileged reads. It does not authorize mutation. Do not use the deploy account or expose the Docker socket to it.
- Collect independent check results so one failed check does not hide the remaining results. After reporting all applicable checks, return a nonzero result if any check failed. Transport errors and unexpected command errors are failures, not successful defaults.
- Emit one stable line for each applicable check and host:

  ```text
  PASS <host-alias> <check-id> <sanitized-detail>
  FAIL <host-alias> <check-id> <sanitized-detail>
  ```

- Do not print secret values, private keys, token files, raw environment contents, or unfiltered command output. Details may include a service state, package version, measured disk/inode use, or a failing policy name. If a host is unreachable, report the access failure and each applicable check that could not run as `FAIL` with a `not evaluated: SSH unavailable` detail.
- A check for a role that is not assigned to a host is not applicable and is not reported for that host. A role assigned by inventory/profile but missing its verification implementation is a failure. Never convert unavailable, malformed, or unknown data into `PASS`.
- Ansible may create temporary remote module files. Ensure those files are removed by normal cleanup; no persistent host configuration, package, service, account, firewall, network, or application state may change.

### Check matrix

| Role/check owner | Applicable checks and pass conditions | Failure conditions |
|---|---|---|
| `common`, `users`, `ssh_hardening` (spec 03) | Admin-key SSH connection succeeds with strict host-key checking; expected `cdo-admin` and `cdo-deploy` accounts exist; effective SSH policy refuses root and password/keyboard-interactive authentication; admin privilege escalation is available for automation reads. | Connection/pin failure, missing or unexpected account, insecure effective SSH policy, or unavailable required privilege. |
| `firewall` (spec 03) | Firewall is active and its effective rules match the selected host's declared SSH source/port policy plus the allowed public web ports. Automatic security updates are active. | Firewall disabled, undeclared ingress, or public database/app/Docker API access. |
| `docker` (spec 04) | Docker Engine is installed and active; Compose v2 is available; daemon has no TCP listener; `edge` and `db` are bridge networks and the `db` subnet matches inventory; running containers publish no host ports. | Missing/inactive runtime, missing or incorrect network/subnet, exposed Docker API, or any published container port. |
| `deploy_runtime` (spec 04) | `cdo-deploy` exists and is not in privileged or Docker groups; the two approved scripts exist, are root-owned, are not deploy-writable, and match the reviewed repository versions; sudoers syntax is valid and grants only the two approved absolute script paths. If the GHCR pull-token file is installed, check only its root ownership and `0600` mode. | Missing, modified, writable, or incorrectly owned script; broad/invalid sudo rule; Docker access; or improperly protected token file. Never read or print token contents. |
| Disk/inode measurement (host verification) | Report used and available disk space and inode use for the required host filesystems. | Required measurements cannot be read. No numeric pressure threshold is invented here; spec 14 must align the check with any approved alert threshold. |
| `nginx`, `certbot` (spec 07) | Nginx configuration test passes and service is active; certificates are valid and have at least 21 days remaining. | Invalid/inactive proxy or a certificate expiring in under 21 days. |
| `postgresql` (spec 08) | PostgreSQL is available and listens only on the approved local and `db` network addresses; reboot ordering is verified by spec 08. | Unavailable service, missing required listener, or a public/unapproved listener. |
| Backup role (spec 13) | Report age of the newest successful backup without exposing repository credentials or snapshot data. | No successful backup or newest backup older than 8 hours. |
| `monitoring_agent` / `collector` (spec 14) | Agent is active and its configured connectivity/last-success signal is healthy, without exposing credentials. | Agent unavailable or no healthy connectivity signal. |

The `roles/<role>/tasks/verify.yml` convention keeps each check with the role it protects. `playbooks/verify.yml` invokes exactly the checks for roles selected by the host's inventory/profile. A later role spec must add its check and tests in the same change as the configure role; the central workflow and output contract remain stable.

### Runbook contract

Create `docs/runbooks/verify-vps.md`. It must explain:

- The prerequisites from specs 01–04, the `Staging`/`Production` choice, and how an exact host, group, or whole-Environment target is selected.
- The safe operational sequence: bootstrap a new host, configure it (check mode first), run verification, resolve failures through the owning role, then repeat the same process for Production with its Environment protection.
- How to inspect per-host results, distinguish a failed check from an unreachable host, and retain sanitized run URL/commit/date evidence.
- That verification is diagnostic only and never repairs a host; operators must use `configure-vps.yml` or the appropriate recovery procedure for changes.
- The role-check extension rule and the deferred Nginx/TLS, PostgreSQL, backup, and monitoring checks owned by their later specs.
- No host credentials, tokens, private keys, or sensitive address data in the runbook or evidence.

## Decisions

| # | Decision | Alternatives | Why | Reversible |
|---|---|---|---|---|
| D1 | Verification uses the admin SSH identity and read-only checks; it never uses the deploy identity or runs configuration tasks. | Use the deploy key; rerun configure in check mode | The admin identity can inspect protected host state, while configure check mode is not a guarantee that every task is read-only. | Yes |
| D2 | An empty `limit` means the complete selected Environment; a non-empty limit is one exact host or group. | Accept Ansible patterns or arbitrary extra arguments | This supports the PRD's host/group/Environment scopes without allowing target expansion or argument injection. | Yes |
| D3 | Role checks are co-located with the configure role and selected from the same inventory/profile mapping. | One central checklist that future roles can forget to update | A role cannot be approved without its corresponding verifier and test, satisfying INF-18. | Yes |
| D4 | The verifier reports all independent failures before returning a failed workflow result. | Stop at the first failed check | Operators receive a useful per-host report without hiding additional failures. | Yes |
| D5 | Disk and inode measurements are reported, but this spec does not invent a numeric pressure threshold. | Add an unsupported threshold | INF-06 and OBS-03 require measurement/alerting but do not define a utilization limit; spec 14 owns alignment with an approved alert policy. | Yes |
| D6 | Checks for later roles are added by those role specs; no placeholder or success-shaped skip is added now. | Implement speculative checks against roles that do not exist | The check must match the delivered role's actual configuration and evidence. | Yes |

## Invariants

| Invariant | How to check |
|---|---|
| A verification run cannot target the other Environment. | Unit-test unknown and cross-Environment host/group limits; assert no secret or SSH step runs. |
| Every SSH connection uses the selected Environment's pinned key and strict host-key checking. | Inspect effective Ansible/OpenSSH settings and reject a disposable-host connection with a mismatched pin. |
| Verification does not mutate persistent host state. | Review every verifier task/module and compare relevant host state before and after a successful disposable-host run. |
| Every applicable check has one explicit result per host. | Assert unique check IDs, one `PASS`/`FAIL` per applicable host/check pair, and an overall nonzero result when any check fails. |
| A configured role without a verifier cannot pass acceptance. | Test role-to-check coverage and fail when a role's `tasks/verify.yml` or integration is absent. |
| Deploy script integrity is checked without exposing script contents or secrets. | Compare remote checksums to the reviewed repository source; inspect output and logs for secret-free results. |
| A host with an unreachable SSH endpoint or unavailable required data is never reported healthy. | Exercise connection and command failures on a disposable host or controlled test fixture. |

## Error behavior

| Situation | Behavior |
|---|---|
| Spec 04 checklist or its disposable-host evidence is incomplete. | Do not run this spec against a VPS; report the unmet prerequisite. |
| Spec-02 dispatch App identity is unknown or not proven. | Do not enable the workflow or guess the actor ID; fail closed. |
| Ref, actor, Environment, inventory, or target validation fails. | Stop in secret-free preflight before Environment credentials or SSH are used. |
| Host key is missing or differs from the committed pin. | Fail closed; do not scan and trust a replacement key. |
| Host is unreachable. | Report SSH access as `FAIL`, report each applicable unrun check as `FAIL`, and fail the workflow. |
| A check fails but later independent checks can still run. | Report all results, then fail the workflow. |
| A required check is missing for a role assigned to the host. | Fail the run/acceptance; do not silently skip the role. |
| A read command errors, returns malformed data, or cannot establish a result. | Report `FAIL` with sanitized detail; never default to `PASS`. |
| Certificate has fewer than 21 days remaining or newest successful backup is older than 8 hours. | The corresponding role check reports `FAIL`. |
| Production approval is not granted. | The Environment-bound job does not start and no Production credential is available. |

## Testing strategy

- Test the secret-free target resolver for both fixed inventories: exact host, exact group, full Environment, malformed value, unknown value, cross-Environment value, empty inventory, and invalid Environment. Confirm invalid cases do not invoke Ansible or SSH.
- Test that a non-main Staging ref is accepted, a Production ref outside `release/*` is rejected, and the proven dispatch App actor is rejected; inspect Environment binding and least-privilege permissions.
- Run workflow lint, the repository naming/secrets checks, `ansible-inventory --list`, `ansible-playbook --syntax-check`, `ansible-lint`, and focused verifier unit tests.
- Test every current role check with passing and failing fixtures. Confirm a deliberately modified deploy script, an invalid sudoers rule, an exposed Docker listener, and a missing/incorrect network fail.
- On a disposable VPS only, run the verifier and compare persistent package, service, account, firewall, network, and checked-file state before/after. Verify that every independent result is emitted and the run exits nonzero after a controlled failure; restore any test-only tampering before closing the task.
- Test a host-key mismatch and an unavailable host. Never use Production or a real service host for negative/fault-injection tests.
- Later role specs must test the certificate-under-21-days and backup-over-8-hours failures, PostgreSQL listener policy, and monitoring connectivity when those roles are delivered.
- Record dated, sanitized evidence without secret values, private keys, or sensitive host details.

## Out of scope

- Any host remediation, bootstrap, configuration, firewall change, service restart, or credential rotation.
- The configure workflow's profile execution, registry/Compose policy, capacity enforcement, and app deployment.
- Implementing Nginx/Certbot, PostgreSQL, backup, or monitoring roles; specs 07, 08, 13, and 14 own those roles and their verification checks.
- Public scanning or external uptime monitoring as part of the Ansible verifier. Any external exposure/probe evidence is handled by the relevant runbook or observability spec.
