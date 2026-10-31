# Checklist for 01_init-cicd_291026/02_dispatch-trust-proof

- [x] Task 1: throwaway-repository - Prepare an isolated app repository, its no-secret Environments, and selected-repository GitHub App access
- [x] Task 2: app-dispatch - Request a bound OIDC token and dispatch the synthetic request from the throwaway app
- [x] Task 3: central-verifier - Verify both proofs before associating the central run with the matching Environment
- [x] Task 4: rejection-tests - Prove invalid proofs, claims, and changed payloads cannot reach the Environment-bound job
- [x] Task 5: evidence-cleanup - Record sanitized results and remove or revoke every test-only resource
