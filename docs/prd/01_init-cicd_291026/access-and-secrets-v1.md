# Module PRD: Environments, Access Control and Secrets (v1)

| Item | Value |
|---|---|
| Parent PRD | `docs/prd/01_init-cicd_291026/prd-v1.md` |
| Module prefix | `SEC` |
| Status | Draft for review |
| Source design | `docs/notes/requirements/02_init-cicd_291026/v5/centraldevops-complete-infrastructure-design.md` (§ references below point to this document) |

## Scope

How GitHub Environments, credentials and approvals are organised across CentralDevOps and the app repositories so that server credentials stay central, app secrets stay with the app, and Production changes are controlled. Backup-specific key custody is in `backup-and-recovery-v1.md`; request authentication is in `central-deployment-v1.md`.

Priority: **Must** = required before Production go-live. **Should** = required before the capability it supports is relied on. **Could** = later phase.

## Must

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| SEC-01 | Every repository (CentralDevOps and each app) has exactly two GitHub Environments, `Staging` and `Production`, mapped to their corresponding Staging and Production VPS targets. There is no Environment per VPS. | Repository settings of CentralDevOps and each onboarded app show exactly these two Environments, and each Environment is mapped to the matching deployment target. | §1 #7, §4.1 |
| SEC-02 | Variable and secret names use `SCREAMING_SNAKE_CASE`, an ownership prefix (`ANSIBLE_`, `VPS_`, `DEPLOY_`, `GHCR_`, `APP_`, `BACKUP_`, `MONITORING_`), the same name in both Environments (the Environment supplies the value), and never `STAGING_`/`PRODUCTION_` prefixes, a `GITHUB_` prefix or generic names such as `TOKEN` or `KEY`. | Every name referenced by a workflow conforms. Only variables and secrets that a workflow actually consumes exist. | §4.2, §4.3 |
| SEC-03 | The provider-issued initial VPS password is a temporary CentralDevOps Environment secret used only by bootstrap; the provider username is a per-host inventory fact. Other credentials are secrets, while ordinary configuration (paths, public keys, host key pins, domains) is variables or committed files. Per-host facts are never GitHub variables. | A review finds no credential stored as a variable or per-host fact as a GitHub variable. The initial password is not stored in inventory, a workflow input, logs, artifacts or an app repository, and is removed after the independent admin-key login succeeds. | §4.2 |
| SEC-04 | Org-level values are used only for credentials with identical scope in both Environments and are restricted to selected repositories. | No org-level secret is visible to repositories other than the selected ones. | §4.2 #7 |
| SEC-05 | The CentralDevOps `Production` Environment requires approval for production infrastructure changes and deployments, and accepts runs only from protected branches matching `release/*`. Those branches have the same protections as `main`. Initially the repository owner is the required approver. The CentralDevOps `Staging` Environment requires no approval and accepts runs from any branch. | A Production deployment or infrastructure run does not start its privileged job until approved, and a run from outside protected `release/*` cannot use the Environment. Staging has no required reviewers and accepts runs from any branch. | §4.1 |
| SEC-06 | The deploy SSH key and the sealed-bundle decryption key exist only as CentralDevOps Environment secrets, with a separate value per Environment. They are never committed as files. | A scan of repository history finds no private key material. The Staging key cannot log in to a Production host, and the reverse. | §4.4, §17 #1 |
| SEC-07 | The admin automation SSH key and temporary provider initial-access password are never usable by the deployment workflow. | The deployment workflow never references the `ANSIBLE_SSH_PRIVATE_KEY` or `VPS_INITIAL_ACCESS_PASSWORD` secrets. | §4.4 |
| SEC-08 | App runtime secrets stay in the app's own Environments. They are encrypted at rest and in transit and are never passed as plaintext through workflow inputs or artifacts. | Inspecting inputs, artifacts and logs of a test deployment shows no plaintext secret value. | §1 #5, §7.2 |
| SEC-09 | An app never holds the registry pull token or the deploy SSH key. | Neither value is present in any app repository or its Environments. | §7.2 |
| SEC-10 | The deployment request is authorised with a dispatch-only GitHub App installed on CentralDevOps with `actions: write` only. No PAT or shared secret is used. The App credentials are org-level secrets restricted to selected repositories, or per-Environment secrets. | The App has only that permission. No PAT exists for dispatching deployments. | §4.5 |
| SEC-11 | The registry pull token is read-only and is installed on each VPS as a root-only file by infrastructure configuration. | The token has only read access to packages and the file on the host is readable by root only. | §4.4 |
| SEC-12 | No secret value appears in workflow logs or artifacts. Secrets are masked and temporary secret material is never uploaded. | Running a deployment with canary secret values leaves no canary value in logs or artifacts. | §8.3, §12.3 |
| SEC-13 | Changes to `apps/**`, `deployment/**`, `roles/**`, `.github/workflows/**`, `.github/CODEOWNERS` and `.github/rulesets/**` require review by code owners before merging into `main` or `release/*`. Both `main` and `release/*` use the same branch protections: pull requests, one approval, code-owner review, required status checks, and no force-push or deletion. | A change to a protected path cannot merge into either protected branch without code-owner review and passing required checks; direct pushes, force-pushes and branch deletion are blocked on both. | §12.2 |
| SEC-14 | Workflows use least-privilege permissions. Third-party actions and the shared `request-deploy` action are pinned to reviewed commit SHAs. Untrusted input is never interpolated directly into shell commands and is validated by strict patterns. | A workflow lint finds no unpinned action and no direct input interpolation in shell steps. | §12.2 |
| SEC-15 | App `Production` Environments accept runs from `main` (or release branches) only. They require no reviewers by default, so a deployment has one approval, in CentralDevOps. | Production deployment needs exactly one approval, in the CentralDevOps `Production` Environment. | §4.1 |
| SEC-16 | Rotation procedures are documented and rehearsed on Staging for: admin and deploy SSH keys, the sealed-bundle key (two recipients accepted during the transition), the registry pull token, the dispatch App key, and the backup repository password. | Each rotation is rehearsed once without a deployment outage, and the procedure is written down. | §15.5 |
| SEC-17 | The README records the GitHub plan and repository-visibility assumption that Environments depend on. | README contains the note. | §1 plan check, §17 #11 |

## Should

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| SEC-18 | Once a deployment team is assigned, it replaces the owner as required Production approver, or is added alongside the owner. | Environment settings reflect the chosen approver model. | §4.1, §17 #6 |

## Could

| ID | Requirement | Acceptance criteria | Ref |
|---|---|---|---|
| SEC-19 | The dispatch App is restricted to dispatching only the deployment workflow if GitHub later supports a narrower permission. | The App cannot dispatch any other CentralDevOps workflow. | §4.5 |
