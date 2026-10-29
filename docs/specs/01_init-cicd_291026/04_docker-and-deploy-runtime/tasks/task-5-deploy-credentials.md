# Task 5: Environment-specific deploy and registry credentials

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Task 4; Production Environment protection verified by spec 01 |
| Needs | CentralDevOps Environment administration; approved read-only GHCR machine credential |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Create and install separate deploy SSH and GHCR credentials without exposing secret values or crossing Environment boundaries.

## Relevant files or references

- Update the name catalog established by spec 01 if either name or its metadata is missing
- Update `.github/workflows/configure-vps.yml` to consume only the admin key and GHCR token
- `docs/design/variables-and-secrets.md` §§1, 4.3, 4.5
- Spec sections: Restricted deploy runtime, Error Behavior

## Proposed approach

1. Generate distinct Staging and Production deploy key pairs; install only the public key in its matching inventory and host. Set each private key as `DEPLOY_SSH_PRIVATE_KEY` in its matching CentralDevOps Environment for the later deployment job; securely remove temporary plaintext key files.
2. Create/use separate GHCR credentials with read-only `read:packages` access. Set `GHCR_PULL_TOKEN` independently in each Environment.
3. Confirm both secret names have the correct kind, scope, and `introduced_by` metadata in the name catalog; do not add secret values. Preserve the existing `forbidden_in` rules for admin and bootstrap credentials.
4. Install the selected Environment's GHCR token with Ansible secret suppression (`no_log: true`, no diff) at the root-only path specified in the spec.
5. Ensure `configure-vps.yml` references `ANSIBLE_SSH_PRIVATE_KEY` and `GHCR_PULL_TOKEN`, never `DEPLOY_SSH_PRIVATE_KEY`. The deploy private key is reserved for the CentralDevOps deployment job in spec 11.

## Acceptance criteria

- The two secrets exist only in their matching CentralDevOps Environments; no repository-level or app-repository copies exist.
- The Staging and Production SSH key pairs and pull tokens are different.
- The host token file is root-owned, mode `0600`, and unreadable by `cdo-deploy`.
- The token can pull a private test package by digest and cannot push packages.
- Canary credential values do not appear in logs, diffs, artifacts, inventory, or committed files.

## Source reference

SEC-06, SEC-07, SEC-11, SEC-12; D-10, D-12, D-13.

## Verify

- Audit GitHub Environment secret names/scopes without reading or printing their values.
- On the disposable host, test read access as root and denied access as `cdo-deploy`.
- Test pull succeeds and push is denied using the read-only token; inspect logs for the canary.

## Out of scope

Admin key rotation, initial provider password lifecycle, age bundle key, app runtime secrets, or production app deployment.
