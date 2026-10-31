# Task 5 Summary: Main Branch Protection

- Added `.github/rulesets/main.json` to `main` through PR #4; the active ruleset is ID `26226141` and covers `refs/heads/main` and `refs/heads/release/*`.
- Required pull requests, one approval, code-owner review, stale-review dismissal, latest-push approval, and the `workflow-lint` and `naming-and-secrets` checks.
- Kept only the documented D6 `aldoawp` pull-request-only bypass. Both required checks passed on PR #4.
- The sole codeowner could not self-approve; PR #4 was merged through the PR with `gh pr merge 4 --merge --admin` under the documented sole-owner exception.
- Scratch `release/*` direct-push, force-push, and deletion attempts were refused. GitHub's effective-rules API confirms the same rules on `main`; destructive attempts against `main` were not made.
- PR #3 completed with a failed `workflow-lint` check and was reported blocked by GitHub; it remained unmerged.
