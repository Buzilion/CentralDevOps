# Configure VPS and Restricted Deploy Runtime Runbook

## Scope and readiness

`configure-vps.yml` is an on-demand infrastructure operation. It does not bootstrap a host, deploy an application, or expose a Docker, PostgreSQL, or application port. Bootstrap and current host-key pin requirements remain in the [bootstrap runbook](bootstrap-vps.md).

The workflow's secret-free preflight rejects an invalid caller/ref, Environment, profile, missing role or inventory fact, empty target, or invalid host/group limit before the Environment-bound job and before SSH. The inventory is fixed by `target_environment`; there is no inventory-path input. The configure job binds to exactly that validated Environment. Production approval happens before the final configure step receives its secrets.

The profile matrix is defined in `deployment/tools/configure-profiles.json` and must match spec 04 exactly. Profiles are all-or-nothing. The workflow never skips missing roles or applies a partial profile. The current spec-04 roles `docker` and `deploy_runtime` do not make a complete profile: later roles such as `monitoring_agent`, `backup`, `nginx`, `certbot`, `postgresql`, and `collector` must be delivered before the profiles that use them can run.

The Staging inventory currently has no target host, and its admin and deploy public-key facts are unconfigured. Do not use a Production host or credential to substitute for the disposable Staging acceptance host. No disposable-host runtime acceptance evidence is recorded here; host install, route-overlap, idempotence, credential-access, and canary-pull/push tests remain deferred.

## Inputs and branch policy

| Input | Contract |
|---|---|
| `target_environment` | Exact `Staging` or `Production`; selects the matching inventory |
| `profile` | Exact `app`, `proxy`, `database`, `monitoring`, or `all-in-one` |
| `limit` | Empty for the selected inventory's full target set, or one exact host alias/group |
| `check_mode` | Defaults to `true`; runs `ansible-playbook --check --diff`. Convergence requires explicitly selecting `false`. |

Staging accepts branch refs. Production accepts `release/*` branch refs only and waits for the Production Environment approval before secrets or host access. Tags are not accepted. The numeric dispatch-App actor is checked in preflight using the identity already proven by spec 02; do not replace or guess this value.

For a limited run, use one exact inventory alias or group. Wildcards, Ansible pattern syntax, comma-separated targets, whitespace, option-like values, and cross-Environment aliases are rejected. Never pass an inventory path or arbitrary Ansible arguments.

## Credentials and inventory

Set credentials only in the matching CentralDevOps GitHub Environment:

- `ANSIBLE_SSH_PRIVATE_KEY` is the selected Environment's admin key. It must use the `base64:` format described in the [variables and secrets guide](../design/variables-and-secrets.md#41-ansible_ssh_private_key), and its public key must match `bootstrap_admin_public_key`.
- `GHCR_PULL_TOKEN` is a separate, read-only package credential with `read:packages` only. Configure uses it only for host provisioning and installs it at `/root/.config/centraldevops/ghcr-pull-token`, owner `root:root`, mode `0600`. The copy task suppresses logs and diffs; the deploy account must not be able to read it.
- `DEPLOY_SSH_PRIVATE_KEY` is not used by `configure-vps.yml`; it is reserved for the later deployment workflow. The deploy public key is a single Ed25519 public key in `deploy_runtime_public_key` under that Environment's inventory. Never commit private keys or token values.

Staging and Production deploy keys and GHCR credentials must be distinct. Generate and set them using the reviewed procedures in the variables and secrets guide. Do not put secret values in command arguments, workflow inputs, inventory, logs, diffs, or artifacts. A names-only audit can use:

```bash
gh secret list --repo Buzilion/CentralDevOps --env Staging
gh secret list --repo Buzilion/CentralDevOps --env Production
```

The Docker inventory facts pin Engine, containerd, Buildx, and the Compose v2 plugin versions, define `docker_db_subnet_cidr`, and declare Docker's default address pools. The current subnet value is a candidate only; the configure role checks the disposable host's routes and Docker networks before creating either shared network. An overlap is a hard failure, not a reason to choose a fallback subnet automatically.

## Running a safe configure

From a reviewed Staging branch, inspect the full inventory in check mode after it has a disposable target and all roles in the selected profile are available:

```bash
gh workflow run configure-vps.yml \
  --repo Buzilion/CentralDevOps \
  --ref "$STAGING_BRANCH" \
  -f target_environment=Staging \
  -f profile=app \
  -f check_mode=true
```

To select one target, add `-f limit="$STAGING_HOST"` where the value is one exact host alias or group from `inventories/staging/hosts.yml`. Leave `limit` empty to target the full selected inventory. The current profile set is incomplete, so preflight is expected to reject these examples before any SSH connection.

After a reviewed check-mode run, profile completion, secret setup, and disposable-host acceptance, an operator may explicitly request convergence by selecting `-f check_mode=false`. Do not run normal configure on a service host until the matching profile has passed check-mode and idempotence acceptance on a disposable host.

For Production, use a `release/*` ref and the same exact input values. The workflow waits at the CentralDevOps `Production` Environment approval gate before accessing `ANSIBLE_SSH_PRIVATE_KEY` or `GHCR_PULL_TOKEN`. Production acceptance is out of scope for spec 04.

## Runtime verification on a disposable host

Run these checks only after the Docker and deploy-runtime roles have converged on a disposable host. Do not perform destructive or negative tests on a service host.

```bash
docker version --format '{{.Server.Version}}'
docker compose version --short
docker network inspect edge db
systemctl show docker.service --property=ExecStart --value
systemctl show docker.socket --property=Listen --value
stat -c '%U:%G %a %n' /run/docker.sock
sudo -l -U cdo-deploy
sudo /usr/sbin/sshd -T | grep '^loglevel'
```

Confirm the Docker service uses Unix socket activation, the socket is `root:docker` with mode `0660`, the `edge` and `db` networks are local bridges, and `db` uses the selected inventory subnet. The subnet validator runs before network creation and rejects overlaps with host routes, Docker address pools, or existing networks.

The deploy account must not belong to `sudo`, `wheel`, `admin`, `docker`, `lxd`, `disk`, `adm`, `shadow`, or `systemd-journal`. On the disposable host, verify the denied paths without printing secret contents:

```bash
sudo -u cdo-deploy docker ps
sudo -u cdo-deploy sudo -n /bin/sh -c id
sudo -u cdo-deploy test -r /root/.config/centraldevops/ghcr-pull-token
sudo -u cdo-deploy sudo -n /usr/local/sbin/centraldevops-deploy
sudo -u cdo-deploy sudo -n /usr/local/sbin/centraldevops-route
```

Each command above is expected to fail. The two sudo entrypoints are fail-closed stubs until spec 11; they must never report success or change state in spec 04. Inspect `/var/log/centraldevops-sudo.log` for command attribution and `journalctl -u ssh.service` for SSH session/key-fingerprint records. The sudo configuration does not enable input/output logging, so secret contents are not captured.

For GHCR acceptance, use only a synthetic canary package on the disposable host. Confirm pull-by-digest succeeds and push is denied. Do not display or record the token. Compare host state before and after check mode, then run the delivered roles again unchanged and record zero changes.

## Failure handling

- **Invalid ref, actor, Environment, profile, role, inventory fact, or limit:** stop. Preflight must fail before the Environment-bound job or SSH; correct the reviewed input or repository state.
- **Pinned package or signature unavailable:** stop without replacing the existing Docker installation. Do not use a floating package version or convenience installer.
- **Invalid or overlapping database subnet:** stop before network creation. Review host routes and declared ranges, then update the inventory through code review.
- **Docker TCP listener or unexpected socket permissions:** do not open a firewall port. Restore the reviewed socket-activation configuration on the disposable host and verify no TCP listener before retrying.
- **GHCR token error:** the task is redacted by Ansible. Check that the selected Environment has a read-only token and rotate it using the documented procedure; never print it.
- **Deploy entrypoint returns nonzero:** expected until spec 11. Do not broaden sudo or replace the stub with deployment behavior here.

## Sanitized acceptance record

No host acceptance run was performed for this implementation. When the Staging disposable-host gate is available, record the following without tokens, keys, host IPs marked sensitive, or runtime data:

| Field | Value |
|---|---|
| Date (UTC) | |
| Environment and disposable alias | |
| Tested roles/profile | |
| Workflow run URL and reviewed commit | |
| Check-mode before/after result | |
| First convergence changed count | |
| Unchanged second-run changed count | |
| Network, socket, sudo, SSH, and token-canary outcomes | |
| Deferred full-profile roles | |
