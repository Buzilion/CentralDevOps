## History (tasks 1-1, compressed)
Task 1 reused TestRepo as the disposable source, verified its Staging/Production Environments, and scoped the Dispatch Proof App secrets to that repository. Task 5 later removed those resources and deleted the remote repository.

## Task 2: app-dispatch — Dispatch a request-bound proof from the test repository

### What was implemented
- Added a temporary manual workflow at `TestRepo-Application/.github/workflows/deploy.yml`, guarded to the intended `main`/Staging source and with minimal workflow permissions.
- Generated bundle bytes at runtime, computed the request-bound audience from the exact environment, image reference, and bundle bytes, requested and masked OIDC tokens, and minted a CentralDevOps-only App installation token in memory.
- Dispatched only to the non-main proof branch. The workflow polled the Actions API to discover the resulting CentralDevOps run URL and emitted sanitized status information.
- Used no third-party actions in the source workflow and never logged or committed tokens, private-key contents, or bundle contents.
- Run date: 2026-11-01 local (GitHub timestamps 2026-10-31 UTC).

### Review findings addressed
GitHub's `workflow_dispatch` response did not provide a run URL or `Location` header. The workflow was updated to poll the Actions API for the dispatched run instead of assuming a URL was returned.

### Current state
The positive source run was [41218412950](https://github.com/Buzilion/TestRepo-Application/actions/runs/41218412950), with CentralDevOps run [41218423509](https://github.com/Buzilion/CentralDevOps/actions/runs/41218423509). The temporary workflow and remote TestRepo repository were removed during Task 5.

### Deferred findings
None specific to this task. The existing D6 pull-request bypass is unchanged and remains tracked under spec 01.
