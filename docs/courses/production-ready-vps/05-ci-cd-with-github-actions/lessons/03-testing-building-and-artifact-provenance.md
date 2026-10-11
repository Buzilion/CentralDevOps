# 03 — Testing, building, and artifact provenance

## Learning objectives

You can design CI checks that are repeatable and meaningful, explain the difference between a build artifact and a cache, and preserve a verifiable link from source revision to release artifact.

## Make CI repeatable

CI should run the same documented commands that developers rely on, under a declared toolchain. Use the language's lockfile and deterministic/frozen install mode where available; pin the runtime/tool version rather than relying on a runner's moving default. Keep scripts in the repository when they are part of the release process so local and automated behavior do not drift.

Order checks to provide useful feedback while preserving correctness: install dependencies, run fast static checks and tests, build the production output, then run applicable image or integration checks. Do not hide failed commands behind `continue-on-error`, broad shell conditionals, or success-shaped fallbacks. A required check should fail the job when it fails. Use explicit service health checks for test databases/queues and ensure test data is disposable.

For a monorepo, select project paths carefully and ensure changes to shared libraries, build scripts, workflow files, or shared configuration trigger the dependent checks. A skipped job should not accidentally make a required release gate appear satisfied. Document any check intentionally omitted and why.

## Artifact and cache are different

An **artifact** is an output intended to be consumed later (for example, a package, test report, or container image). A **cache** is an optimization that may be absent, stale, or evicted; never rely on it for correctness or deployment. Upload build/test artifacts only when they have a clear consumer, retention period, and sensitivity classification. Do not upload secrets, `.env` files, private keys, or raw production data.

Prefer building a container once and passing its immutable image identity to the deploy stage. If using GitHub Actions artifacts between jobs, bind the downloaded artifact to the expected run/commit and avoid rebuilding it at deploy time. Verify that the deployment selects an artifact produced by the successful, authorized release process.

## Identify the bytes, not just the label

Names such as `latest`, `main`, or `production` are mutable references. They are convenient pointers, not reliable release identities. Include the source commit in the image tag (often a full commit SHA) and record the registry's image digest. A digest such as `sha256:...` identifies content; deploy by digest where the tooling supports it. A release tag is useful for people but should not be the only identity used by a running production service.

Keep enough metadata to answer: which source commit, workflow run, build configuration, and image digest produced this deployment? Store run links or a sanitized deployment record. If supply-chain attestations are used, verify they are created by the expected workflow and understand what they prove; an attestation does not make an unreviewed source trustworthy.

## Supply-chain and job boundaries

Pin actions to reviewed full commit SHAs and review dependency-update changes. Limit permissions per job. A test job should not have package publishing rights; a publisher should not receive production SSH credentials unless it also deploys. Prefer separate jobs with explicit `needs` relationships and pass only the minimum artifact metadata. A compromised dependency in a broad-permission job can misuse every credential available to that job.

Do not print environment variables to debug a failed build. Avoid verbose commands that reveal registry tokens or configuration. Masking cannot reliably redact transformed, encoded, or partial secrets.

## Practical checkpoint

Implement required CI commands against the application's declared toolchain. Demonstrate that a deliberately failing check fails the workflow, then restore the code and show the expected green run. Record the commit, checks, and exact image/artifact identity. Complete [Task 02 — Add pull-request and branch verification](../tasks/02-add-pull-request-and-branch-verification.md).

## Knowledge check

1. Why is a cache never sufficient proof that a release artifact is correct?
2. What does an image digest establish, and what does it not establish?
3. How could a workflow accidentally allow code from a test dependency to publish an image?
4. What evidence makes a deployed image traceable to source?

## References

- [GitHub Actions: Storing and sharing data from a workflow](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)
- [GitHub Actions: Dependency caching](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [GitHub Actions: Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
