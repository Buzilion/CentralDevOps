# Module PRD: Infrastructure Provisioning, Configuration and Verification (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `INF` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

Turning a manually created Sumopod VPS into a hardened, correctly configured, verifiable host for a given Environment (`Staging` or `Production`), and keeping it that way. Covers the three on-demand infrastructure operations (bootstrap, configure, verify), per-environment inventories, the host security baseline and the restricted deploy runtime that the deployment module relies on. VPS creation itself stays manual (Sumopod has no API).

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase, contract only.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| INF-01 | An operator can bootstrap a new VPS for a selected Environment on demand, first connecting with the provider-supplied username and password. Bootstrap creates separate named admin and deploy accounts, applies OS updates and a base firewall, then installs the admin public key. | On a fresh VPS, the provider credentials establish initial access; both accounts exist, the base firewall is active, and admin key login works. The operation can only target `Staging` or `Production`. | §6.1 |
| INF-02 | SSH hardening is applied only after a second, independent login using the installed admin public key has succeeded. | If the admin-key login check fails, the run stops with the initial access still working and no hardening applied. If it passes, root login and password login are refused afterwards. | §6.1, §12.1 |
| INF-03 | An operator can converge a host onto one profile: `app`, `proxy`, `database`, `monitoring` or `all-in-one` (= app + proxy + database). | Each profile applies exactly the role set defined in §6.2. A second consecutive run reports zero changes. | §6.2 |
| INF-04 | Configure offers a dry run that shows the planned differences without changing the host. | A dry run leaves host state unchanged and outputs the diff. | §6.2 |
| INF-05 | Configure accepts an optional host or group limit, validated against the selected Environment's inventory before any connection. | A limit naming an unknown host, or a host from the other Environment, is rejected with a clear error before any SSH connection. | §6.2 |
| INF-06 | An operator can run a read-only verification for a host, a group or a whole Environment. It reports PASS or FAIL for: SSH access and expected users, firewall state, Docker and Compose, the `edge` and `db` networks, Nginx configuration and service, certificate expiry, PostgreSQL and its listen addresses, deploy scripts present, root-owned and unmodified, monitoring connectivity, disk and inode usage, newest backup age, and the deploy-user sudoers entry. | One PASS/FAIL line per check per host; any FAIL fails the run; the run changes nothing on the host. A deliberately modified deploy script, a certificate expiring in under 21 days, and a backup older than the backup-age alert threshold (8 h) are each reported FAIL. | §6.3 |
| INF-07 | Each Environment has its own inventory. Roles are expressed as groups; one all-in-one host is a member of several groups. Per-host facts (address, user, groups, ports, private IP, capacity budget) live only in inventory or the registry. | No workflow hard-codes a host name or address. Moving a role to another host requires only group membership and registry placement changes. | §4.2, §6.4 |
| INF-08 | The inventory used by any operation is derived from the selected Environment; it is never typed in by the operator. | A `Staging` run can never operate on a `Production` host, and the reverse. | §4.3, §8.1 |
| INF-09 | SSH host keys are pinned in a reviewed, committed per-environment file and every SSH session uses strict host-key checking. A fresh key scan over the same connection is never trusted. | Connecting to a host presenting an unexpected key fails. | §4.4 |
| INF-10 | Host security baseline: key-only SSH; only ports 80 and 443 public (SSH restricted by source IP or VPN where practical); PostgreSQL, app ports and the Docker API never public; automatic security updates enabled. | An external port scan of a configured host shows only 80 and 443 (plus SSH per the access policy). Password and root SSH logins are refused. | §12.1 |
| INF-11 | Docker Engine and Compose are installed, and the `edge` network and the `db` network (fixed subnet) exist before any app is deployed. Published container ports are not used, so the firewall and Docker agree. | Verification confirms both networks. No container publishes a port to a public address. | §9.4, §11.1, §12.1 |
| INF-12 | A restricted deploy runtime is installed: an unprivileged deploy account that is **not** in the `docker` group, permitted to run only the two server-side deploy and route scripts through sudo with validated arguments. The scripts are root-owned and not writable by the deploy account. | The deploy account cannot run Docker directly, cannot run any other sudo command and cannot modify the scripts. Invalid arguments are rejected by the scripts. | §8.5 |
| INF-13 | Admin and deploy identities and keys are separate. | The admin key is never available to the deployment workflow; the deploy key cannot log in as admin. | §1 #8, §4.4, §8.5 |
| INF-14 | Infrastructure operations run only on demand. They are never part of an app deployment, and they reject dispatches made by the deployment-dispatch GitHub App identity. | Dispatching bootstrap, configure or verify with the dispatch App token fails at the start of the run. | §1 #8, §4.5, §12.2 |
| INF-15 | Infrastructure operations use only credentials scoped to the selected Environment, and Production infrastructure changes require approval. | A Production configure run waits for approval before using any credential. | §4.1 |
| INF-16 | Proof that access survives hardening is recorded on a disposable VPS before any Staging or Production host is hardened. | A recorded successful bootstrap with a verified second login on the disposable VPS. | §16 step 3 |
| INF-17 | Runbooks exist for creating a new VPS and for changing VPS configuration (dry run, Staging, verify, then Production with approval). | Both runbooks exist and were followed for the first Staging host. | §15.1, §15.4 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| INF-18 | Every role added to configure has a matching verification check. | A role has no merge approval without its verification check. | §16 step 5 |
| INF-19 | Brute-force protection (fail2ban or equivalent) is enabled only after its effect on the legitimate access path has been tested. | A test run shows the deploy and admin paths are not blocked by it. | §12.1 |
| INF-20 | The per-host capacity budget (physical RAM minus the reserve for OS, Docker, Nginx, PostgreSQL and the collector) is declared in inventory for use by the capacity check. | Every host in inventory declares a budget. | §9.3 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| INF-21 | A WireGuard role provides private networking between hosts if Sumopod's private network does not connect separate VPS instances. | Two test hosts communicate over the private link only. | §10.1 |
| INF-22 | The `app`, `proxy` and `database` profiles are exercised on separate hosts. | A split-host environment passes verification without workflow changes. | §14.2 |
