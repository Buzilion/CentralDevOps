## History (tasks 1-3, compressed)
The disposable TestRepo workflow produced a request-bound OIDC proof, and the temporary CentralDevOps verifier validated GitHub's signature, exact source claims, expected App actor, and audience before allowing its Environment job. Task 5 removed the proof resources after live testing.

## Task 4: negative-tests — Prove tampering and untrusted dispatches are rejected

### What was implemented
- Added deterministic generated-key tests for malformed or mismatched audiences, invalid signatures/issuer/expiry, missing or incorrect source claims, unexpected actors, and Production ref policy. The suite passed 11/11.
- Verification command: `node --test .github/scripts/verify-dispatch-proof.test.mjs` (11/11 passed). Live cases used the temporary TestRepo deploy workflow and CentralDevOps verifier files listed in Task 3.
- Ran live rejection cases for a changed image, changed bundle, tampered OIDC signature, and unexpected dispatch actor.
- Confirmed every rejected authorization job stopped before the Environment job. Source and CentralDevOps logs contained no JWT-like values, private-key headers, payload dumps, or artifacts.
- Run date: 2026-11-01 local (GitHub timestamps 2026-10-31 UTC).

| Case | Source run | CentralDevOps run | Rejection |
|---|---:|---:|---|
| Changed image | [41218567992](https://github.com/Buzilion/TestRepo-Application/actions/runs/41218567992) | [41218578339](https://github.com/Buzilion/CentralDevOps/actions/runs/41218578339) | `audience_binding` |
| Changed bundle | [41218629132](https://github.com/Buzilion/TestRepo-Application/actions/runs/41218629132) | [41218639965](https://github.com/Buzilion/CentralDevOps/actions/runs/41218639965) | `audience_binding` |
| Tampered OIDC signature | [41218716196](https://github.com/Buzilion/TestRepo-Application/actions/runs/41218716196) | [41218727161](https://github.com/Buzilion/CentralDevOps/actions/runs/41218727161) | `oidc_signature` |
| Unexpected actor | Not applicable | [41218786651](https://github.com/Buzilion/CentralDevOps/actions/runs/41218786651) | `dispatch_actor`, before proof parsing |

### Review findings addressed
The negative tests use generated keys and runtime-generated bundle bytes rather than checked-in secrets or payloads. Actor rejection is independent of proof parsing.

### Current state
All proof workflows and test code have been removed from the default branches. The live run records were retained as evidence; no credentials or proof payloads were retained.

### Deferred findings
None within the specified negative-test scope. Production deployment authorization was not exercised.
