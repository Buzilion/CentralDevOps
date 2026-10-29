# Task 5: Staging rotation rehearsals

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/15_onboarding-and-go-live/spec.md` |
| Depends on | Task 4 |
| Needs | Approved Staging credentials, the completed rotation runbook, and operational access to the relevant Staging systems |
| Summary | Write `summaries/task-5-summary.md` when this task closes |

## Goal

Rehearse each mandatory SEC-16 credential rotation on Staging, prove the replacement works, and confirm the application remains available.

## Relevant files or references

- `docs/runbooks/credential-rotation.md`
- `docs/design/variables-and-secrets.md` §11
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-16)
- v5 design §15.5

## Proposed approach

1. Rehearse admin SSH key and deploy SSH key replacement separately. Verify the appropriate admin/verification or Staging deployment path before removing each old public key.
2. Rehearse the age-key transition with old and new recipients accepted concurrently. Deploy a Staging request through the overlap, verify decryption and result, then remove the old recipient only after success.
3. Rehearse the registry pull token replacement and verify the configured host can pull the approved Staging image before revoking the old token.
4. Rehearse dispatch App key replacement and verify a Staging dispatch is accepted and correlated with the correct central run before deleting the old key.
5. Rehearse Restic password rotation in the Staging repository; verify a backup and restore with the replacement before removing the old repository key.
6. For each rehearsal, record only the credential class, date, sanitized run/evidence link, pass/fail, outage impact, and rollback result. Keep secret values, private keys, tokens, plaintext runtime data, and sealed bundles out of all records.
7. If an optional S3, monitoring, or app-secret rotation is included, record it separately from the six mandatory SEC-16 rehearsals.

## Acceptance criteria

- Each mandatory SEC-16 credential class has one successful Staging rehearsal.
- The Staging app remains available during the rehearsals; no deployment outage occurs.
- Every old credential is removed only after the replacement is verified, and every rehearsal has a recorded rollback outcome.
- Age-key overlap and Restic backup/restore verification both pass.
- No secret value appears in logs, artifacts, task summaries, or the rotation record.

## Source reference

SEC-16; v5 §15.5; `variables-and-secrets.md` §11.

## Verify

- Check the Staging deployment/verification and Restic evidence for each rotation.
- Confirm all six mandatory rotation rows have a dated pass and no outage.
- Check that the old credentials were retired only after successful replacement verification.

## Out of scope

Production credential rotation, changing production access, or claiming success for a rehearsal that was skipped or only simulated.
