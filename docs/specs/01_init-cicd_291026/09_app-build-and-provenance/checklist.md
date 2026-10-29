# Checklist for 01_init-cicd_291026/09_app-build-and-provenance

Implementation is blocked until every task in `01_foundation-and-access/checklist.md` is checked off. Complete the tasks below in order. At each task close, add its sanitized `summaries/task-<n>-summary.md`; do not write implementation summaries before the work is done.

- [ ] Task 1: build-workflow-contract - Establish the app-owned manual workflow, source-ref resolution, protected workflow ref, and least-privilege job boundaries
- [ ] Task 2: test-gated-ghcr-publish - Test the resolved commit before publishing the canonical image and `sha-<full-commit>` tag
- [ ] Task 3: build-provenance-attestation - Attest the pushed digest with `actions/attest` and verify the selected source commit in SLSA provenance
- [ ] Task 4: digest-metadata-output - Report the full digest and upload the versioned metadata-only artifact after attestation succeeds
- [ ] Task 5: disposable-build-acceptance - Prove positive and negative paths, document the operator contract, and clean up temporary resources
