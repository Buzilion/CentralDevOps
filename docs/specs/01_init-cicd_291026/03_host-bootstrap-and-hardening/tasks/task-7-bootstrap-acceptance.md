# Task 7: Bootstrap acceptance audit

| Item | Value |
|---|---|
| Spec | `docs/specs/01_init-cicd_291026/03_host-bootstrap-and-hardening/spec.md` |
| Depends on | Tasks 1 to 6 |

## Goal

Audit every requirement in spec 03, retain evidence, and establish the safe handoff to spec 04.

## Relevant files or references

- `docs/runbooks/bootstrap-vps.md`
- Spec sections: Requirements H-01 to H-13, Invariants, Error behavior, Testing strategy
- `docs/specs/01_init-cicd_291026/04_docker-and-deploy-runtime/` (next spec; do not begin until this checklist closes)

## Proposed approach

1. Run syntax, lint, inventory, workflow, catalog, and negative tests from Tasks 1–5.
2. Audit the disposable VPS proof and all evidence required by Task 6.
3. Confirm no secrets or fake host data are committed and no credential appears in workflow logs or artifacts. Confirm the admin private-key secret is documented as `base64:` plus a single-line Base64 encoding, and that raw key text is rejected.
4. Confirm the initial password was removed from the tested Environment after key access was verified.
5. Confirm the dispatch App identity check and Production approval gate are active.
6. Record PASS/FAIL against H-01 through H-13 in the runbook. Fix in-scope defects or leave the task and spec blocked; do not mark a failed requirement complete.
7. Mark checklist tasks complete only after their acceptance criteria and evidence are satisfied.

## Acceptance criteria

- Every requirement H-01 through H-13 has dated evidence or a clear blocked status, including reset-host pin re-verification.
- Disposable-host hardening proof is recorded and no Staging/Production hardening occurred before it.
- Workflow and inventory isolation, strict host-key checking, secret lifecycle, and least privilege are verified.
- Fresh/reset hosts bootstrap on 22, transition through a proven dual-listener state, and finish with sshd/UFW/provider firewall on 4671 only; already-managed hosts remain on 4671. The SSH Fail2ban policy is one day after two failures within one hour, and service-host activation remains gated by recorded disposable proof.
- No open failure blocks spec 04 from starting; the spec-01 prerequisite remains satisfied.
- The checklist accurately reflects completed work.

## Current disposition

The repository owner attests that the post-reset disposable-host hardening proof was completed manually; the attestation in `docs/runbooks/bootstrap-vps.md` is sufficient to unblock local spec 04 implementation. Detailed per-requirement artifacts are waived for this handoff only and must not be inferred from the historical audit. This disposition does not claim that this acceptance-audit task or spec 04 runtime acceptance is complete, and it does not satisfy the `DISPOSABLE_VPS_PROOF_COMMIT` gate for non-disposable service-host operations.

## Verify

Run the complete targeted test set defined by this spec and review the evidence log before marking this acceptance-audit task complete. The attestation above unblocks local spec 04 implementation but does not replace the evidence required to close this task.

## Out of scope

Docker/runtime configuration, `verify-vps.yml`, and later role verification.
