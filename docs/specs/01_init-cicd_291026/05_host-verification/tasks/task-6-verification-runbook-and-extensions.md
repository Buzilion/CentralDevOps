# Task 6: Verification runbook and role extensions

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/05_host-verification/spec.md` |
| Depends on | Tasks 1–5 |
| Needs | Reviewed bootstrap/configure runbooks from specs 03 and 04 |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Document safe verification operations and make the ownership of future role checks explicit so no configure role can be added without its corresponding check.

## Relevant files or references

- Create `docs/runbooks/verify-vps.md`
- `docs/runbooks/bootstrap-vps.md` (spec 03)
- `docs/runbooks/configure-vps.md` (spec 04)
- `docs/specs/01_init-cicd_291026/00_spec-roadmap.md`
- Spec 05 sections: Runbook contract, Check matrix

## Proposed approach

1. Document Environment and exact host/group/whole-inventory target selection, prerequisites, Production protection, and how to start the workflow.
2. Explain the operational sequence after bootstrap or configure: verify, resolve failures through the owning workflow/role, then verify again.
3. Document the result format, failure/unreachable handling, evidence retention, and the rule that verification never repairs a host.
4. Record the role-check extension contract: every new configure role adds `roles/<role>/tasks/verify.yml`, tests, and verifier integration in the same change.
5. Assign deferred checks to their owning specs: Nginx/certificate expiry to spec 07, PostgreSQL listeners to spec 08, backup age to spec 13, and monitoring connectivity/any approved disk-pressure threshold to spec 14.
6. Do not create placeholder checks for roles that do not exist. State that certificate expiry under 21 days and a newest backup older than 8 hours must fail when their owning checks are delivered.
7. Include only sanitized examples. Do not include host credentials, private keys, token values, or sensitive addresses.

## Acceptance criteria

- `docs/runbooks/verify-vps.md` describes prerequisites, scope selection, approval behavior, result interpretation, and recovery/escalation path.
- The runbook says explicitly that verification is read-only and remediation uses the owning workflow.
- Every future configure-role owner and check obligation is named with its roadmap spec.
- The 21-day certificate and 8-hour backup thresholds are preserved exactly; no unsupported disk/inode threshold is invented.
- No sensitive host or credential data is added.

## Source reference

INF-06, INF-17, INF-18; HV-06 to HV-08; v5 design §§15.1, 15.4, 16 step 5.

## Verify

- Review all referenced paths against the repository and roadmap.
- Check that the runbook's operational order matches the bootstrap/configure runbooks and Production Environment protections.
- Confirm examples and evidence instructions contain no sensitive values.

## Out of scope

Implementing future Nginx, PostgreSQL, backup, monitoring, or alerting roles and checks.
