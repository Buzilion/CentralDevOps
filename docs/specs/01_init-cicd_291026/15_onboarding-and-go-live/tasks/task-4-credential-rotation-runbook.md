# Task 4: Credential rotation runbook

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | Task 1 |
| Needs | Final secret names/scopes and operational procedures from specs 03-05, 11-14 |
| Summary | Write `summaries/task-4-summary.md` when this task closes |

## Goal

Document safe, reversible Staging-first procedures for every credential class required by SEC-16.

## Relevant files or references

- Create `docs/runbooks/credential-rotation.md`
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-06, SEC-10, SEC-11, SEC-16)
- `docs/design/variables-and-secrets.md` §§4-5, 11
- v5 design §§4.4-4.5, 12.1, 15.5
- Specs 03-05, 11, 13, and 14

## Proposed approach

1. Write a separate ordered procedure for the admin SSH key, deploy SSH key, sealed-bundle age key, registry pull token, dispatch App private key, and Restic repository password.
2. For every procedure, state where the new credential is created, where its replacement is installed, how Staging verifies it, when the old credential may be removed, and how to roll back if verification fails.
3. For age-key rotation, document the old/new recipient overlap and require successful decryption/deployment through the transition before removing the old recipient.
4. For the Restic password, include the repository key-add/update/verification/removal sequence and protect the recovery copy in the approved password manager.
5. Document the additional S3, monitoring, and app-secret rotation patterns from `variables-and-secrets.md` where those credentials are used; do not treat them as substitutes for SEC-16's mandatory set.
6. Add a sanitized rehearsal record format containing credential class, Environment, date, verification result, outage impact, and rollback outcome. Never record the credential or secret value.

## Acceptance criteria

- All six SEC-16 credential classes have explicit step-by-step procedures.
- The old known-good credential is retained until its replacement passes the relevant Staging check.
- The age-key procedure accepts both intended recipients during transition.
- The Restic procedure verifies backup and restore before retiring the old repository key.
- The guide identifies the relevant Environment and credential scope and contains no real credentials.

## Source reference

SEC-06, SEC-10, SEC-11, SEC-16; v5 §§4.4-4.5, 15.5; `variables-and-secrets.md` §11.

## Verify

- Walk each procedure against the matching workflow, Ansible role, deployment path, or backup runbook.
- Confirm that a failed verification has a rollback path that retains a working credential.
- Search the document and examples for tokens, private keys, passwords, or other real secret values.

## Out of scope

Performing the Staging rehearsals (Task 5), rotating Production credentials, or changing the secret ownership model.
