# 01 — Workflow model, triggers, runners, and trust boundaries

## Learning objectives

You can explain how a GitHub Actions event becomes a workflow run, distinguish jobs from steps and runners, choose triggers that match release intent, and identify which code and credentials are trusted at each stage.

## The delivery path

Continuous integration (CI) automatically checks a proposed or changed revision. Continuous delivery (CD) keeps a release deployable; continuous deployment additionally promotes it to an environment automatically. A workflow is not inherently safe because it is automated: its trigger, code revision, runner, permissions, secrets, and deployment target together define its risk.

The core execution model is:

```text
GitHub event
  -> workflow file selected from the event's revision/ref
    -> jobs scheduled on eligible runners
      -> steps execute sequentially in a job
        -> artifacts, images, or deployment effects cross job boundaries
```

A workflow is a YAML file under `.github/workflows/`. A workflow can contain multiple jobs; each job normally runs on a separate runner. Steps within one job share that runner and execute in order. A later step can use files created by an earlier step in that same job, but a different job must explicitly download an artifact or retrieve an image from a registry. `needs` defines job dependencies and gates downstream jobs on upstream success. It is not a substitute for testing that an artifact is the one being deployed.

GitHub-hosted runners are disposable virtual machines maintained by GitHub. They are convenient for builds, but do not assume files, installed software, or local state persist between jobs or runs. A self-hosted runner is infrastructure you operate: its persistence, software, network access, cleanup, and compromise recovery become your responsibility. Never place a self-hosted runner on the production VPS merely for convenience, especially if it can execute code from pull requests.

## Select triggers by intent

Common events include:

- `pull_request`: validate a proposed change before merge. Treat the checked-out contribution as untrusted code.
- `push`: validate commits pushed to a branch. Scope the branch filter deliberately.
- `release`: react to GitHub release activity; choose whether a published release, rather than a draft or prerelease, is eligible.
- `workflow_dispatch`: permit an authorized person to start a run manually. Validate any input and do not let an input become an arbitrary shell command, image, host, or path.
- `workflow_call`: reuse a workflow, but audit its caller/callee permissions and secrets as one system.

Use separate workflows or clearly separated jobs for pull-request verification and production deployment. A pull-request workflow should not receive production secrets. Do not use `pull_request_target` to check out and execute untrusted pull-request code with the base repository's privileges. A trigger can run against an attacker-controlled change; consider which revision supplies the workflow and code before granting write permissions or secrets.

Tags and release events express different policies. A tag name is not proof that the source was reviewed, tested, or authorized; protect release branches/tags and constrain environment deployment rules. A manually selected ref is also not automatically a safe release. The deployed commit/image must be identified and verified.

## Trust boundaries and permissions

GitHub assigns a `GITHUB_TOKEN` to a run. Declare only needed permissions. A typical verification job needs `contents: read`; an image-publishing job may additionally need `packages: write`. Prefer job-level permissions so a test job cannot publish or deploy merely because another job needs that capability. Start with a deny-by-default top-level `permissions: {}` where supported, then grant narrow job permissions.

Secrets are capabilities. Any process that can read a secret can disclose or misuse it; log masking is a convenience, not a security boundary. A secret exposed to a shell step is exposed to the code and tools that step runs. Limit secrets to a protected deployment job/environment, avoid them in pull-request workflows, and never print them, pass them in command-line arguments, or copy them into artifacts.

Actions are executable dependencies. Pin third-party actions to a reviewed full commit SHA, not a mutable branch or tag, and update pins deliberately. Review what an action can access, monitor updates, and avoid unnecessary actions. GitHub's `permissions` constrains the token but does not constrain a long-lived SSH key exposed to a compromised action.

## Practical checkpoint

For the repository you will deploy, draw the event-to-deployment path and annotate each step with the source ref, runner, permissions, artifacts or image, secrets, and target. Mark where untrusted code could execute. Complete [Task 01 — Inspect the application and define the release contract](../tasks/01-inspect-the-application-and-define-the-release-contract.md).

## Knowledge check

1. Why can files created in one job not be assumed to exist in another?
2. What is the security difference between a PR verification job and a production deploy job?
3. Why do a protected tag and a successful workflow each provide useful but incomplete release evidence?
4. What additional responsibilities appear when using a self-hosted runner?

## References

- [GitHub Actions: Understanding GitHub Actions](https://docs.github.com/en/actions/about-github-actions/understanding-github-actions)
- [GitHub Actions: Events that trigger workflows](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows)
- [GitHub Actions: Security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
