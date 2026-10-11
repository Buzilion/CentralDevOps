# 08 — Reliability exercises and continuous improvement

## Learning objectives

You can design bounded reliability exercises, test a complete recovery path rather than a single command, use evidence to find operational gaps, and keep production readiness current as the service changes.

## Exercise the real procedure safely

Reliability claims should be supported by an exercise or incident evidence. Choose scenarios that matter to the deployed system: application process exit, failed release, unavailable non-production dependency, low-disk warning, backup restore, expired test credential, or monitoring notification failure. Do not fill a production disk, kill the production database, revoke the only administrator credential, or disrupt real users merely to prove a point.

Before each exercise, document:

- Objective and explicitly excluded scope.
- Environment, owner, participants, start/end time, and approval.
- Expected detection and action, safety limit, abort/stop condition, and communication method.
- Recovery/rollback steps, independent access path, and evidence location.
- What constitutes success, including an externally verified result where relevant.

Prefer staging, synthetic test conditions, provider test functions, or a reversible low-risk production change approved by the owner. Verify normal health and backup status before a test that could affect state. A tabletop discussion is useful for decision-making but does not prove that credentials, tools, monitoring, or restore artifacts work.

## Test end-to-end, not one component

A deployment rehearsal should include artifact selection, preflight, release, health gate, failure decision, rollback or forward-fix, and public validation. A restore drill should test backup retrieval, decryption/access, application compatibility, data validation, and measured recovery—not merely file existence. An incident exercise should test alert receipt, acknowledgment, runbook retrieval, escalation, action authority, and recovery verification. Record elapsed time and constraints; compare actual results with the declared RTO/RPO or response expectations.

Keep test failures safe and informative. Stop at the defined boundary if the exercise risks real data or service. If the intended alert does not fire, treat that as a monitoring gap and restore normal coverage before ending. Do not leave test credentials, temporary firewall openings, disabled alerts, or synthetic routes behind.

## Convert findings into operational improvements

For each gap, record impact, evidence, owner, due date, completion condition, and whether it changes a procedure, automation, test, alert, or architecture. Prioritize based on user harm, likelihood, recovery difficulty, and cost. Verify the fix by repeating the smallest relevant part of the exercise. Avoid tracking vague actions such as “improve monitoring”; specify a result another operator can check.

Update the affected docs, automation, and checklists together. Record architecture and procedure changes with the release or infrastructure change that introduced them. Revisit known assumptions after changes to the app, database, domain, provider, backup path, monitoring service, or access model.

## Recognize the limits of a single VPS

A well-operated VPS can still fail because of provider, host, storage, network, account, or regional problems. Backups, off-host monitoring, and tested rebuild instructions reduce impact but do not make the application continuously available. Set expectations accordingly. If actual service needs exceed what a single-host recovery model can meet, define the required availability and recovery targets first, then design additional failure domains proportionate to those needs.

## Practical checkpoint

Complete [Task 08 — Run a production operations readiness review](../tasks/08-run-production-readiness-review.md) after all other tasks and close or explicitly accept its findings.

## Knowledge check

1. What can a tabletop exercise validate that a restore drill cannot, and vice versa?
2. Why should a test have an abort condition and independent recovery path?
3. Which evidence demonstrates that a corrective action is complete?
4. What reliability limit remains even after an effective single-VPS recovery plan?

## References

- [Google SRE Workbook — Testing for Reliability](https://sre.google/workbook/testing-reliability/)
- [Google SRE Book — Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/)
- [Google SRE Book — Postmortem Culture: Learning from Failure](https://sre.google/sre-book/postmortem-culture/)
