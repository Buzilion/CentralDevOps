# CentralDevOps
Centralized repository for reusable DevOps configurations, CI/CD workflows, infrastructure automation, and server provisioning using GitHub Actions and Ansible.

## Reusable workflows

- [build-and-test.yml](.github/workflows/build-and-test.yml) runs the Node/npm checks, Docker build, health verification, and GHCR publication for callers that follow that build contract. Callers provide the GHCR image name; workflow-dispatch callers can also provide a release environment and SemVer version to publish generated GitHub release notes after successful verification. Development and staging releases use non-production prerelease tags.
- [deploy-to-vps.yml](.github/workflows/deploy-to-vps.yml) accepts application deployment settings and runs the shared Ansible deployment playbook directly.

## Ansible

Shared inventories, playbooks, and the generic application deployment role are maintained under [`ansible/`](ansible/README.md).
