# Task 6: Recovery runbook and certificate limits

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/13_backup-and-recovery/spec.md` |
| Depends on | Tasks 1–5; specs 07, 08, 11 and 12 checklists complete |
| Needs | Current registry, inventory, DNS records and official certificate-authority limit documentation |
| Summary | Write `summaries/task-6-summary.md` when this task closes |

## Goal

Give two authorized recovery operators a complete, timed lost-VPS procedure, including DNS, digest selection, durable-data restore and certificate-rate-limit handling.

## Relevant files or references

- Create `docs/runbooks/backup-and-disaster-recovery.md`
- `docs/prd/01_init-cicd_291026/backup-and-recovery-v1.md` (BKP-11 to BKP-15)
- `docs/prd/01_init-cicd_291026/routing-and-tls-v1.md` (RTE-12)
- Spec 11 deployment-record task and spec 12 release/rollback runbook
- v5 §§13.3–13.4

## Proposed approach

1. Document the incident trigger, required operator roles, recovery-copy access, Environment isolation and manual Sumopod VPS creation. Sumopod VPS provisioning and DNS changes remain manual.
2. Write the ordered recovery procedure: create the replacement VPS; update DNS or reassign an IP; bootstrap/configure; restore PostgreSQL and approved durable app data; redeploy every app through the normal authorized flow at its last known-good full digest; run `verify-vps.yml` and smoke tests.
3. Include a time budget for every step, including persistent-file restore and certificate issuance. Use measured Staging restore data; the total recovery target, including the selected DNS strategy, must remain at or below 4 hours.
4. Set Production DNS A/AAAA TTL to 300 seconds before go-live and document how operators verify authoritative/public TTL and update records during recovery. If the DNS provider cannot honor the TTL, block go-live pending a reviewed alternative; do not assume the previous IP can be reassigned.
5. Count active Production domains from the registry and consult the current official Let's Encrypt rate-limit documentation. Record the checked date, exact domain count, a numeric conservative issuance-wave size and retry window; do not leave generic placeholders.
6. Use the CA staging endpoint for all issuance drills. If Production issuance is rate-limited during a real recovery, stop retries for affected domains, preserve any valid restored certificate, keep domains without a valid certificate unavailable rather than serving HTTP, continue unaffected recovery work and retry only after the documented window.
7. Explain how operators obtain the last known-good digest from the app run history and off-host deployment record without consulting the lost host. Do not use tags or bypass Production approval.

## Acceptance criteria

- The runbook is executable by two authorized operators without relying on undocumented host-local information.
- Every recovery step has a time budget, owner/evidence field and a safe failure path; the full target is 4 hours or less.
- The Production DNS TTL decision is exactly 300 seconds, verified before go-live, with no dependency on IP reassignment.
- The runbook lists a numeric Production domain count and certificate issuance wave size based on the current registry and current official CA limits.
- CA-staging use for drills and the rate-limit fallback are explicit; no procedure disables TLS or repeatedly retries a rate-limited request.
- Each app's recovery digest can be selected from app run history and off-host records and is redeployed through the existing authorization path.

## Source reference

BKP-11 to BKP-15; RTE-12; parent PRD Q3 and Q4; v5 §§13.3–13.4.

## Verify

- Walk through the runbook using a disposable Staging target and confirm every prerequisite can be found without host-local state.
- Independently verify the Production domain count against the registry and the rate-limit reference against the official CA page on the recorded check date.
- Review that DNS uses manual change control, app deployment uses full digests, and no Production credential or certificate is used in the drill.
- Confirm each step's time budget sums to no more than 4 hours when measured in the Staging drill.

## Out of scope

Automated VPS provisioning or DNS updates, Production certificate issuance as a test, and changing the RTE-12 CA or routing implementation.
