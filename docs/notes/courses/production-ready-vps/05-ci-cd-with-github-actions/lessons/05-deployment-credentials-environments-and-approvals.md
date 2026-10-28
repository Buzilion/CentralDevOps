# 05 — Deployment credentials, environments, and approvals

## Learning objectives

You can protect a production deployment with environment-scoped access, explain SSH host and client authentication, and select a credential design with a bounded blast radius.

## Separate who is connecting from which host it is connecting to

SSH authenticates both sides:

- **Client authentication:** the runner proves its identity with a client private key (or another configured method). The matching public key is authorized for a specific server account.
- **Server authentication:** the runner verifies the VPS host key, which proves it reached the intended SSH server rather than an impostor.

Keep these checks distinct. Store a dedicated deployment private key as a protected production-environment secret (or use a short-lived identity mechanism where your infrastructure supports it). The corresponding public key should authorize a dedicated deployment account, not root or a human's personal account. Restrict the account's permitted operations as much as the deployment design allows. A Docker-capable account can often gain effective root on that host; treat membership in the `docker` group as privileged, not as ordinary least privilege.

Pin the expected SSH host public key after verifying its fingerprint through a trusted, independent channel such as the provider console or a known-good admin session. Keep the verified `known_hosts` entry in protected configuration or an environment variable/secret. Do not accept any host key returned by an unauthenticated `ssh-keyscan` during each deployment; that merely trusts whoever answered the network request at that moment. Do not disable host-key checking.

Never commit a private key. Do not reuse a developer's key, the Ansible provisioning key, or the registry pull token for application deployment. Rotate and revoke the deployment key independently. Make sure the workflow does not expose the private key in logs, artifacts, caches, or command-line text.

## GitHub environments as a deployment gate

Create a GitHub environment such as `production` and put deployment-only secrets and variables there. Configure required reviewers, prevent self-review where supported and appropriate, restrict which branches/tags may deploy, and consider a wait timer. Organization plan and repository visibility can affect which protection rules are available; inspect the actual settings and do not assume a protection rule exists because a workflow names an environment.

Referencing an environment causes the deployment job to wait for its protection rules and makes its environment secrets available only after the rules pass. Keep build and test jobs outside that environment and without production secrets. This reduces accidental exposure but is not a sandbox: once approved, the deployment job's code can use its secrets. Review the workflow and the exact commit/ref being deployed before approval.

Separate values from credentials. Non-secret values can be environment variables/variables if disclosure is acceptable; passwords, private keys, and tokens are secrets. Never print values for debugging. Secret masking may not catch transformed values. Do not pass secrets through untrusted outputs or persist them as build artifacts.

## Restrict network reachability

The runner must reach SSH on the VPS. GitHub-hosted runner egress ranges can change and may be broad; do not assume a stable single source address. Choose a network access pattern that fits the VPS provider and threat model: narrowly managed allowlisting where maintainable, an authenticated private network/tunnel, or a controlled runner with explicit hardening. A self-hosted runner has persistent-host risks and should never run untrusted PR code with production network access. Keep only the required port open and preserve independent administrative recovery access.

GitHub OIDC is useful when a target service trusts GitHub-issued short-lived tokens, but it does not automatically create an SSH identity for a VPS. Do not claim OIDC security while still using a static SSH private key; document the credential actually used.

## Practical checkpoint

Configure a protected production environment with a test-only or not-yet-active deploy credential. Verify that an unapproved run cannot access environment secrets, that the intended ref is eligible, and that a known-host mismatch fails closed. Complete [Task 04 — Protect production deployment access](../tasks/04-protect-production-deployment-access.md).

## Knowledge check

1. What does the SSH host key prove, and what does the client key prove?
2. Why is `ssh-keyscan` at deployment time not a host-identity verification procedure?
3. What does a protected environment gate, and what does it not make safe?
4. Why is adding a deployment account to the Docker group a significant privilege grant?

## References

- [GitHub Actions: Using environments for deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Actions: Managing environment secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [OpenSSH: ssh_config](https://man.openbsd.org/ssh_config)
