# Task 5: Protected bootstrap workflow

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Task 4; spec-02 dispatch identity proof must be available before acceptance |

## Goal

Expose the tested bootstrap phases through one on-demand workflow that is isolated to the selected Environment and host.

## Relevant files or references

- Create `.github/workflows/bootstrap-vps.yml`
- Update `.github` secret-name catalog from spec 01 if required
- `docs/design/variables-and-secrets.md` §§2–4.1, 4.10
- v5 design §§4.4–4.5, 6.1, 12.2
- Spec sections: Workflow contract; Decisions D1, D2, D5

## Proposed approach

1. Use `workflow_dispatch` with only exact Environment choice and required exact host alias inputs.
2. Add a secret-free preflight job that validates the actor, Environment, and target host against the fixed input-to-inventory mapping, plus the host pin and dependency installation, before any SSH step. Gate the Environment-bound job on successful preflight so invalid input cannot bind a dynamic Environment. In that job, compare `ANSIBLE_INVENTORY_PATH` with the same fixed mapping, check out the same reviewed commit, and install the pinned dependencies on its own runner before SSH.
3. Resolve the dispatch App identity from the completed spec-02 proof and reject it before the credential-using job. Fail closed if the identity is not known.
4. Bind the credential-using job to the selected GitHub Environment. Use least-privilege `contents: read`; Production approval must gate access to Production credentials.
5. Use the temporary password only for initial access; use `ANSIBLE_SSH_PRIVATE_KEY` only for independent admin proof and hardening. Ensure both secrets are masked and never become workflow inputs, command arguments, or artifacts.
6. Pin actions to reviewed 40-character SHAs and pin runner dependencies. Pass event inputs through environment variables with strict validation; no direct `${{ }}` interpolation in shell.
7. After the independent admin-key proof succeeds, clearly instruct the operator to remove `VPS_INITIAL_ACCESS_PASSWORD` from the selected Environment. Do not give the workflow secret-administration permissions. If proof fails, do not request password removal.
8. Run actionlint, zizmor, the spec-01 name checker, and the workflow's negative tests.

## Acceptance criteria

- Only `Staging` and `Production` are accepted; the inventory path and credentials are selected by the GitHub Environment.
- Unknown/cross-environment targets fail before SSH.
- Production secrets are unavailable until the Production approval gate is satisfied.
- Workflow rejects the spec-02 dispatch App identity.
- The workflow does not reference password/admin key from deployment workflows, and the name catalog records correct secret kind/owner.
- CI and workflow lint checks pass with no unpinned actions or direct shell interpolation of inputs.

## Verify

Use workflow lint plus a non-privileged `workflow_dispatch` preflight test. Verify Production Environment approval gating in GitHub settings without using or printing Production secrets. Exercise the full credential workflow only on the disposable host in Task 6.

## Out of scope

Configure/verify workflows, self-deleting secrets, app deployment, and changes to Environment protection rules.
