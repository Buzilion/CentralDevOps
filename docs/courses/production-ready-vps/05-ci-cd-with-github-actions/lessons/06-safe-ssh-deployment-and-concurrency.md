# 06 — Safe SSH deployment and concurrency

## Learning objectives

You can design a small, auditable deployment path from GitHub Actions to the VPS, constrain the remote command surface, and prevent conflicting releases from deploying simultaneously.

## Keep responsibilities separate

Ansible establishes the operating-system baseline: users, SSH policy, Docker, firewall, directories, and other reviewed host configuration. GitHub Actions builds and releases the application. The deployment mechanism connects those responsibilities but should not silently reconfigure the OS on every release.

For a single VPS, a simple first delivery path is:

```text
Protected release workflow
  -> verifies and selects an immutable image digest
  -> connects through verified SSH
  -> asks a narrowly privileged server-side deploy entry point to apply that release
  -> checks the application health and records the outcome
```

The VPS can pull the image directly using a read-only registry credential stored on the server. Keep the production Compose file and runtime secrets on the VPS under administrator-controlled ownership. Update only the image reference for a release; do not upload an `.env` file from a workflow or rebuild on the host.

## Bound the remote interface

Avoid giving the CI identity an unrestricted interactive root shell. Prefer a dedicated account and a fixed, reviewed server-side deployment script or wrapper with a narrow interface, such as accepting only a validated image digest for the expected image. If privilege escalation is needed, scope it to the exact approved entry point, understand argument validation and file ownership, and test the wrapper as the deployment account. A forced SSH command can further constrain a key, but it must be designed so clients cannot bypass restrictions through command arguments, forwarding, PTY, or another login method.

Do not construct remote shell commands by concatenating untrusted branch names, release notes, workflow inputs, or repository metadata. Treat all text from the workflow as data. Validate the image repository and digest format on the server as well as on the workflow side. Hard-code or administratively configure the allowed image repository, Compose project, and target service; do not allow caller-supplied paths or arbitrary Compose files.

Use the runner's SSH client carefully: load the private key from the protected secret without printing it, use a pinned host key, disable agent/port forwarding and interactive prompts when unnecessary, and fail on connection/authentication errors. Evaluate every third-party deployment action like executable code with access to the job's secrets. A few explicit OpenSSH commands can be easier to audit than a large action abstraction.

## Serialize production changes

Two runs deploying different releases at once can interleave image pulls, Compose updates, health checks, and rollback. Use a production-specific workflow concurrency group and do not cancel a deployment after it has started modifying the server. Concurrency is a mutual-exclusion mechanism, not a durable FIFO release queue or a substitute for checking which release is current: GitHub may replace pending runs in a concurrency group. Design what should happen when a newer release arrives while one is running, and ensure an old manually dispatched run cannot silently roll production backward.

Make the release candidate explicit. A protected environment approval should show the selected commit and image digest. Validate that the selected image came from the authorized publisher and successful checks. For manual dispatch, constrain the ref and validate inputs; do not allow arbitrary image names or server addresses.

## Change the service with controlled state

The server-side deploy operation should record the previously running digest, pull the requested digest, apply the Compose change, wait for the actual readiness condition, and return a nonzero status on failure. Keep current and previous configuration in a recoverable form. Use `docker compose config` or equivalent validation before applying when feasible. Avoid destructive volume removal, broad prune commands, or schema rollback as routine deployment actions.

For a single VPS, a short interruption during service replacement may be acceptable. State this explicitly. Do not describe an in-place replacement as zero-downtime. If downtime is unacceptable, first design and test a separate traffic-switching topology rather than adding complex orchestration by assumption.

## Practical checkpoint

Implement the least-privileged path in a staging/test target first. Prove the account can perform only the approved deployment operation, that malformed or wrong-repository image references are rejected, and that two deployment attempts cannot overlap. Complete [Task 05 — Deploy a selected image through a constrained SSH path](../tasks/05-deploy-a-selected-image-through-a-constrained-ssh-path.md).

## Knowledge check

1. Why should the application workflow not also become the server-provisioning workflow?
2. Which untrusted values could turn an SSH command into arbitrary remote execution?
3. Why does deployment concurrency not guarantee every release is deployed in order?
4. What does a successful container start prove that a readiness check does not?

## References

- [GitHub Actions: Control workflow concurrency](https://docs.github.com/en/actions/using-jobs/using-concurrency)
- [GitHub Actions: Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [OpenSSH: sshd authorized_keys format](https://man.openbsd.org/sshd)
