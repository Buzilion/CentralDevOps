# Task 5: Environment-specific deploy and registry credentials

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/spec.md` |
| Depends on | Task 4; Production Environment protection verified by spec 01 |
| Needs | CentralDevOps Environment administration; approved read-only GHCR machine credential |

## Goal

Create and install separate deploy SSH and GHCR credentials without exposing secret values or crossing Environment boundaries.

## Relevant files or references

- Update the name catalog established by spec 01
- Update `.github/workflows/configure-vps.yml` Environment secret references
- `docs/design/variables-and-secrets.md` §§1, 4.3, 4.5
- Spec sections: Restricted deploy runtime, Error Behavior

## Proposed approach

1. Generate distinct Staging and Production deploy key pairs; install only the public key in its matching inventory and host. Set the private key as `DEPLOY_SSH_PRIVATE_KEY` in the matching CentralDevOps Environment, then securely remove the temporary plaintext key.
2. Create/use a dedicated GHCR credential with read-only `read:packages` access. Set `GHCR_PULL_TOKEN` independently in each Environment.
3. Add both secret names with the correct kind, scope and introducing spec to the name catalog; do not add secret values.
4. Install the selected token with Ansible secret suppression (`no_log: true`, no diff) at the root-only path specified in the spec.
5. Confirm the deploy workflow references neither `ANSIBLE_SSH_PRIVATE_KEY` nor `VPS_INITIAL_ACCESS_PASSWORD`; those credentials remain infrastructure-only.

## Acceptance criteria

- The two secrets exist only in their matching CentralDevOps Environments; no repository-level or app-repository copies exist.
- The Staging and Production SSH key pairs and pull tokens are different.
- The host token file is root-owned, mode `0600`, and unreadable by `cdo-deploy`.
- The token can pull a private test package by digest and cannot push packages.
- Canary credential values do not appear in logs, diffs, artifacts, inventory, or committed files.

## Source reference

SEC-06, SEC-07, SEC-11, SEC-12; D-10, D-12.

## Verify

- Audit GitHub Environment secret names/scopes without reading or printing their values.
- On the disposable host, test read access as root and denied access as `cdo-deploy`.
- Test pull succeeds and push is denied using the read-only token; inspect logs for the canary.

## Out of scope

Admin key rotation, initial provider password lifecycle, age bundle key, app runtime secrets, or production app deployment.
