# Task 7: App request acceptance

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/12_app-deploy-request/spec.md` |
| Depends on | Tasks 1 to 6; specs 10 and 11 checklists complete |
| Needs | Disposable or approved Staging app, Staging credentials/host, previous known-good digest, and safe synthetic canary values |
| Summary | Write `summaries/task-7-summary.md` when this task closes |

## Goal

Prove the app request, sealing, dispatch, polling, and digest rollback end to end without weakening Environment protections or exposing secrets.

## Relevant files or references

- `.github/actions/request-deploy/`
- `<app-repository>/.github/workflows/deploy.yml`
- `docs/runbooks/app-release-and-rollback.md`
- `docs/prd/01_init-cicd_291026/app-release-v1.md` (REL-01, REL-05 to REL-14)
- `docs/prd/01_init-cicd_291026/access-and-secrets-v1.md` (SEC-08, SEC-09, SEC-12, SEC-15)
- Specs 02, 09, 10, and 11 acceptance summaries

## Proposed approach

1. Confirm all roadmap gates and the selected Staging app/host are ready. Use a disposable or explicitly approved app and synthetic values; do not relax branch rules, approvals, or permissions.
2. Run the app's manual build and retain its full digest. Run `deploy.yml` for Staging, verify the corresponding CentralDevOps run succeeds, and confirm the app summary links to that exact run.
3. Test a tag and malformed digest. Confirm each fails before dispatch. Test an over-cap synthetic bundle and confirm no dispatch API call or artifact/storage upload occurs.
4. Test wrong-Environment decryption and the old/new recipient overlap with synthetic keys. Confirm the central OIDC verifier rejects altered Environment, digest, or bundle bytes before the deploy job.
5. Deploy a second known-good Staging digest and manually rerun `deploy.yml` with the prior digest. Confirm both requests use the normal central authorization and deployment path and the final running digest is the requested previous digest.
6. Use synthetic canary secrets and inspect app/central logs, summaries, artifacts, and temporary-file cleanup. Confirm no plaintext value, token, bundle content, server credential, or pull token leaked to the app.
7. Exercise Production only when the actual CentralDevOps Production approval and required credentials can be honored. Never remove the approval gate to make the test pass.
8. Record sanitized run URLs, commits, dates, and PASS/FAIL results in this task's summary; do not store canary values or token/payload contents.

## Acceptance criteria

- A manual Staging deployment succeeds by digest and the app run reports its own central run URL/result.
- Tag/malformed digest and oversized-bundle tests fail before dispatch; oversized requests use no alternate transport.
- Altering any request-bound field invalidates authorization before the central deploy stage.
- The matching age key decrypts the bundle; the other Environment's key does not; the rotation overlap works.
- A manual rollback to the previous Staging digest succeeds through the same app workflow and central authorization path.
- Canary values are absent from logs, summaries, artifacts, and committed files; app repositories contain no deploy SSH key or registry pull token.
- Production approval behavior remains intact; any unrun Production case is clearly marked as not exercised rather than passed.
- Sanitized evidence is recorded in `summaries/task-7-summary.md`.

## Source reference

REL-01, REL-05 to REL-14; SEC-08, SEC-09, SEC-12, SEC-15; v5 §§7.2, 8.1–8.4, 15.3, 15.6.

## Verify

- Capture and compare the app and matching CentralDevOps run URLs, source IDs, Environment, and final digest.
- Inspect request logs/API-call assertions for rejected inputs and payloads; do not capture token or payload bodies.
- Review app and central logs, artifacts, and summaries for canary values and plaintext request material.
- Verify the final Staging release is the previous digest and the production approval configuration is unchanged.

## Out of scope

Re-proving the central OIDC verifier or deployment rollback implementation beyond its spec 10/11 acceptance; Production rollout without its approval; and changes to app migration behavior.
