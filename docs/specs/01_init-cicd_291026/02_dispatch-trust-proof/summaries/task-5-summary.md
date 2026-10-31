## History (tasks 1-4, compressed)
TestRepo was prepared with scoped App credentials, then used to dispatch a runtime-generated, request-bound OIDC proof to a temporary CentralDevOps verifier. The verifier validated the trusted GitHub claims and App actor before its Staging Environment job; one positive path and four live rejection paths passed. Generated-key tests passed 11/11. Temporary workflows and credentials were removed after evidence collection.

## Task 5: evidence-cleanup — Record proof evidence and remove temporary resources

Evidence and cleanup verified on 2026-11-01 local (GitHub run timestamps 2026-10-31 UTC).

### What was implemented
- Recorded sanitized positive and negative results, verified claims, Environment approval, test results, and cleanup status in this summary.
- Removed TestRepo's selected organization secrets, repository secrets, Staging/Production Environments, and temporary workflow. Deleted the remote `Buzilion/TestRepo-Application` repository; a repository API request returned HTTP 404.
- Removed the CentralDevOps proof workflow and verifier/test scripts from the default branch, and deleted the remote proof branches. The default branch now has only the normal lint workflow.
- Retained the organization-owned Dispatch Proof App installed only on CentralDevOps for future dispatch work. Its TestRepo-selected organization secrets were deleted, leaving no TestRepo credential access. No key or token values were read or recorded.
- The local TestRepo clone is retained in the workspace with only `README.md` and `.gitkeep` in its checked-out tree.

### Sanitized evidence

| Evidence | Result |
|---|---|
| Positive source run | [41218412950](https://github.com/Buzilion/TestRepo-Application/actions/runs/41218412950) |
| Positive CentralDevOps run | [41218423509](https://github.com/Buzilion/CentralDevOps/actions/runs/41218423509), branch `feature/02_dispatch-trust-proof`, SHA `c5057aca3fcc7bd19327f8a76cd276b5b1b8f277` |
| Verified source claims | `Buzilion/TestRepo-Application`; `deploy.yml@refs/heads/main`; `refs/heads/main`; `Staging`; source run `41218412950`, attempt `1` |
| App actor | `buzilion-dispatch-proof[bot]` |
| Audience comparison | Expected and observed matched: `centraldevops-deploy:89dd504437f107c6f4738279255dc093f5937825b0d1d6c2b2c83c2dcdca48de` |
| Environment approval | CentralDevOps Staging required reviewer approval; approval was honored. Environment secret and variable inventories were empty. |
| Negative paths | Changed image and bundle rejected at `audience_binding`; tampered signature rejected at `oidc_signature`; unexpected actor rejected at `dispatch_actor` before proof parsing. All authorization failures skipped the Environment job. |
| Automated tests | Generated-key verifier suite: 11/11 passed. |
| Leak audit | No JWT-like values, private-key headers, payload dumps, or artifacts in scanned logs. No deployment credentials, VPS access, tokens, private-key contents, or bundle contents were logged or committed. |
| Cleanup | Organization secrets and Environments removed; TestRepo remote deleted; temporary workflows/scripts and remote proof branches removed. |

The source-repository run IDs were recorded before TestRepo deletion; GitHub may no longer serve those run pages. The positive run used the non-production Staging Environment and did not access deployment secrets, variables, or VPS resources. CentralDevOps branch protection and Environment rules were not changed; the TestRepo proof Environments were removed during cleanup. Required `workflow-lint` and `naming-and-secrets` PR checks passed; the existing PR-only `aldoawp` bypass was used for the temporary proof PRs.

### Current state
The TestRepo remote is absent (HTTP 404). The Dispatch Proof App remains selected only for CentralDevOps. Temporary proof code and TestRepo credential access are absent from the default branches and organization secrets.

### Deferred findings
The pre-existing D6 `aldoawp` pull-request bypass remains tracked under spec 01; it was not changed as part of this proof. No deployment-system or production credential was tested.
