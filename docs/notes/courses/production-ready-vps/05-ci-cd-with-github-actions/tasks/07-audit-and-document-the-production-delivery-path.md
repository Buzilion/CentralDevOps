# Task 07 — Audit and document the production delivery path

## Outcome

Demonstrate that an authorized release can be traced, deployed, verified, and recovered using a maintained workflow with documented boundaries and no undocumented personal access.

## Prerequisites

- Complete Tasks 01–06.
- Read [Lesson 08 — Auditing, maintenance, and operational evidence](../lessons/08-auditing-maintenance-and-operational-evidence.md).
- Have an authorized reviewer/operator available for the production-environment review.

## Procedure

1. Review every workflow trigger, ref filter, `permissions` declaration, `needs` dependency, action SHA, shell interpolation, secret use, runner/network boundary, environment rule, and concurrency group.
2. Review package publisher/puller identities, visibility, digest and retention, SSH client/host authentication, deploy account privileges, remote interface ownership, runtime-secret location, and key rotation/revocation steps.
3. Verify required checks are enforced by repository rules and production environment settings are actually enabled. Confirm a failed check, wrong ref, unknown host key, invalid image identity, or missing approval fails closed.
4. Complete one authorized release through the intended process. Record the protected source commit, workflow run, approver, image digest, target alias, verification result, deployment time, and rollback reference.
5. Rehearse the recovery runbook on the safe target if not already done in Task 06. Confirm another authorized operator can identify the deployed version and explain how to halt and recover it.
6. Remove any temporary credentials, package grants, runner registrations, test releases, or access rules created for practice. Rotate credentials if they may have been exposed during setup.
7. Set owners and review intervals for workflow/action updates, deploy-key rotation, package-access review, and production environment reviewers. Record unresolved issues as blockers, not as passed controls.

## Acceptance criteria

- [ ] An authorized reviewer can trace the deployment from source commit through workflow run to running image digest.
- [ ] No unnecessary token permission, secret, mutable action reference, unverified SSH host, or arbitrary remote command remains.
- [ ] Wrong refs, failed CI, invalid image identities, missing approval, and host identity mismatches do not deploy.
- [ ] Rollback is recoverable by digest and has been rehearsed safely; migrations have a separate plan.
- [ ] Temporary practice credentials and privileges are removed or rotated.
- [ ] A different authorized operator can follow the sanitized runbook without relying on one person's undocumented credentials.

## Deliverable

A sanitized production deployment record, final workflow/security review, and maintenance/incident runbook with owners and review intervals. Do not commit secrets, private keys, raw VPS identifiers, or unredacted production logs.
