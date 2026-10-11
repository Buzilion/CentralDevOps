# Task 02 — Add pull-request and branch verification

## Outcome

Every eligible proposed change receives trustworthy CI feedback from the application's real test and build commands without production access or release-publishing privileges.

## Prerequisites

- Complete Task 01 and resolve the commands/toolchain needed for CI.
- Read [Lesson 03 — Testing, building, and artifact provenance](../lessons/03-testing-building-and-artifact-provenance.md).
- Have permission to edit workflow files and configure required checks in the application repository.

## Procedure

1. Add a focused workflow under `.github/workflows/` with deliberate `pull_request` and protected-branch `push` filters. Ensure changes to shared libraries, build scripts, and workflow files trigger the relevant checks if the repository is a monorepo.
2. Pin the required language/runtime versions. Install using the lockfile's deterministic mode and run the exact required lint/type-check/test/build commands from the release contract.
3. Set workflow/job permissions explicitly and narrowly (normally read-only source access). Keep production environment access, SSH credentials, and package write permission out of this workflow.
4. Treat pull-request code as untrusted. Do not use `pull_request_target` to check out and execute the contributor's code. Do not interpolate branch names, titles, or other untrusted event text directly into shell code.
5. Make mandatory checks fail the job on failure. Use explicit dependency service readiness for integration tests. Keep caches optional and secret-free.
6. Use full-SHA action pins and review the action source/permissions. Ensure the required status-check names are stable for branch protection.
7. Run a successful change, then deliberately cause a harmless test/build failure in a disposable branch and confirm the workflow becomes red. Revert the test-only change.

## Acceptance criteria

- [ ] Pull requests and intended protected-branch updates trigger the defined checks.
- [ ] A successful run proves all required tests and a production build passed for the checked-out revision.
- [ ] A deliberately failing check fails the job and prevents downstream release work.
- [ ] The job has no production secrets and no unnecessary token write permissions.
- [ ] Actions are pinned to reviewed full commit SHAs; no required check is silently skipped.
- [ ] The workflow does not execute untrusted contribution code in a privileged trigger context.

## Deliverable

A CI workflow and sanitized run evidence showing its trigger, source revision, toolchain, required checks, and both positive and negative test results. Record the exact required status-check names for branch protection.
