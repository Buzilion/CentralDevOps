# Checklist for 01_init-cicd_291026/02_dispatch-trust-proof
- [ ] Task 1: throwaway-repository - Prepare an isolated app repository and selected-repository GitHub App access for the proof
- [ ] Task 2: app-dispatch - Request a bound OIDC token and dispatch the synthetic request from the throwaway app
- [ ] Task 3: central-verifier - Verify both proofs before associating the central run with the matching Environment
- [ ] Task 4: rejection-tests - Prove invalid proofs, claims, and changed payloads cannot reach the Environment-bound job
- [ ] Task 5: evidence-cleanup - Record sanitized results and remove or revoke every test-only resource
