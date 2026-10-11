# Task 04 — Protect production deployment access

## Outcome

Make production deployment credentials available only to an authorized, protected workflow and ensure the runner authenticates the intended VPS host.

## Prerequisites

- Complete Task 03 and identify the intended deployment account and network path.
- Read [Lesson 05 — Deployment credentials, environments, and approvals](../lessons/05-deployment-credentials-environments-and-approvals.md).
- Preserve a separate, tested administrative and provider-console recovery path.

## Procedure

1. Create a GitHub `production` environment. Restrict eligible deployment refs to the intended protected release branch/tag policy; configure required reviewers and other available protection rules. Verify repository/organization plan support rather than assuming a rule is active.
2. Generate a dedicated deployment SSH key pair. Keep the private key only in the protected environment secret; install its public key for a dedicated, non-root VPS deployment account. Do not reuse personal, Ansible, or registry credentials.
3. Restrict the server account to the approved deployment operation as far as the design permits. Document effective privileges: Docker access may confer root-equivalent control of the VPS. Ensure the account cannot modify its own trusted deploy script or host configuration.
4. Independently verify the VPS host-key fingerprint, then configure the exact expected `known_hosts` entry for the deployment job. Never disable host checking or trust a key scanned dynamically during the production run.
5. Choose a network path that allows the selected runner to reach SSH while limiting exposure. Document GitHub-hosted runner address limitations or the isolation/maintenance risks of a self-hosted runner. Never allow untrusted PR jobs to use a production-connected self-hosted runner.
6. Add environment access only to the deployment job. From an unapproved test run, verify the secret is unavailable. Verify that an unexpected ref is blocked and that a deliberately incorrect known host causes SSH to fail closed.
7. Document key rotation/revocation, operator ownership, and recovery if the CI credential is exposed.

## Acceptance criteria

- [ ] Production secrets are environment-scoped and unavailable to CI/test jobs and unapproved deployments.
- [ ] Environment reviewers/ref restrictions are enabled and verified in repository settings.
- [ ] The deploy identity is distinct, non-root, and its effective Docker/OS privilege is explicitly understood.
- [ ] Host identity is pinned from an independently verified fingerprint; a mismatch fails closed.
- [ ] SSH reachability is limited to the deliberate deployment design and administrative recovery still works.
- [ ] No secret, fingerprint-verification bypass, or private infrastructure detail is committed to logs/artifacts.

## Deliverable

A sanitized access-control record describing environment rules, eligible refs, reviewer policy, runner/network model, SSH account restrictions, host-key verification, secret scope, rotation owner, and recovery path. Never record the private key or secret value.
