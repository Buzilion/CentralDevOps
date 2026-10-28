# VPS Platform Requirements Brainstorm

## Summary

The goal is an operator-led process for preparing already-acquired VPS capacity and promoting application releases through controlled environments. The initial scope is two VPSs, application containers, and a DEV → STAGING → PROD release path. The main unresolved requirements are measurable timing and availability criteria, application-specific health checks, detailed stage gates, and precisely which host-baseline changes are permitted.

## Candidate Outcome

> An authorized operator can register existing VPS capacity, review its state, prepare it through approved phases, and deploy an eligible application release. Each run identifies its targets and release, records approvals and outcomes, reports partial failures clearly, and promotes the same release through the required environments.

## Decisions Captured

- **Capacity model:** VPS acquisition is manual. Automatic elasticity is not in first-release scope. Start with two VPSs; five-VPS parallel scale-up is a later goal.
- **Initial topology:** one VPS is shared by DEV and STAGING; PROD has a dedicated VPS. Multiple applications may share a VPS.
- **Workloads:** deploy application containers. Hosting databases is out of the initial scope.
- **Pilot:** `OutboundMarketing-Application` is the first deployment pilot.
- **Host preparation:** the first usable release audits and reports host findings. The owner approves any fixes before they are applied. Sensitive access/firewall/network changes are deferred to a later guarded phase.
- **Security outcomes:** limit exposed services, apply security updates, remove or disable unused/default accounts, and record administrative/preparation activity. The owner is the only administrator in the current phase; provider-console access is the recovery path. Apply updates during approved maintenance windows. Only public-facing application entry points should be publicly reachable.
- **Promotion:** releases proceed DEV → STAGING → PROD. DEV → STAGING requires owner approval and a manual trigger. PROD requires STAGING health checks and owner approval. In the current owner-operated phase, the owner may trigger and approve their own production deployment.
- **Artifact:** STAGING and PROD are intended to use the same DEV-built release rather than rebuilding it.
- **Deployment success and time:** the pilot process starts and its application endpoint responds. The target is under 10 minutes from deployment workflow trigger to that health check passing; VPS acquisition is excluded.
- **Partial rollout:** continue processing independent targets. Leave successful hosts on the new release and failed hosts unchanged; report partial success and resolve failures before considering the rollout complete.
- **Recovery:** support redeploying a previously successful application release. Persistent data/schema recovery is a later concern.
- **Shared-host risk:** DEV and STAGING should remain logically independent, but shared host outage/resource risk is temporarily accepted and must be documented.
- **Service targets:** measure the internal apps' baseline first, then set availability and recovery expectations.
- **Maintenance impact:** brief interruption is acceptable for current internal applications; the acceptable duration is not yet quantified.

## Gap Analysis

- **Deployment speed is only partly defined.** The start, completion event, and under-10-minute target are set for the pilot. Confirm whether the target is for one app deployment or all apps assigned to both initial VPSs, and whether it covers the deploy stage only after CI has passed.
- **Shared environments create a real failure domain.** Separate release status does not isolate DEV from STAGING host failure or resource contention. Document this temporary limitation and decide the acceptable impact during staging work.
- **Host readiness and remediation need acceptance criteria.** Auditing and reporting are agreed, but the exact baseline checks, which low-risk fixes are allowed, and what owner approval covers are not. The existing bootstrap plan defers firewall, SSH, account, and network changes; align the product boundary with that plan.
- **Promotion policy needs complete gates.** The path, manual DEV-to-STAGING trigger, STAGING health checks, and owner PROD approval are set. Required CI checks, DEV/STAGING health criteria, manual smoke testing, and emergency exceptions remain open.
- **Artifact provenance should be explicit.** The same DEV-built release should move unchanged into later environments. Define how operators identify the release, prove what is running, and retain the prior known-good release for recovery.
- **Partial deployment needs a service policy.** The per-host behavior is set, but the minimum healthy capacity for keeping the app in service and the owner for retry/recovery decisions are not.
- **The pilot's runtime and service expectations are unknown.** Define its endpoint/dependency checks, expected downtime, external data dependencies, and alert response. Availability and recovery targets should follow baseline measurement.
- **Operations and lifecycle responsibilities are missing.** Decide who receives alerts and owns patching, backup/restore, incident response, host replacement/retirement, access removal, and data sanitization. These can be explicitly deferred, but should not remain accidental assumptions.
- **Constraints are missing.** Initial OS/provider support, provider neutrality, cost limits, and which app entry points are public need to be identified.

## Host Preparation: Remaining Questions

These are requirements and operating-policy questions, not implementation choices.

1. Which baseline findings may be fixed after owner approval in the first release (for example, security updates or unused/default accounts), and which findings must only be reported until a later phase?
2. What evidence must be checked before a sensitive access/firewall change is eventually allowed: provider-console recovery availability, a maintenance window, successful DEV testing, or all of these?
3. For each application/environment, which entry points must be public and which services must remain internal-only?
4. What must each activity record contain, and who reviews failed changes or security alerts?
5. What is the acceptable maintenance interruption for DEV, STAGING, and PROD? Are updates/restarts treated differently from application deployments?

## Remaining Questions

1. Does the under-10-minute deployment target apply to one app on one VPS, or all selected applications across the two initial VPSs? Does it cover only deployment after CI passes?
2. For `OutboundMarketing-Application`, should the health check only confirm the app endpoint responds, or also verify a key dependency? Which endpoint or user-visible behavior defines success?
3. What exact CI and deployment checks are required before DEV and STAGING are considered successful? Is a manual smoke test required before owner approval for PROD?
4. Can an urgent release ever bypass DEV → STAGING → PROD? If so, what owner approval and audit record are required?
5. When a rollout is partial, what minimum healthy host count/capacity is acceptable for continuing service, and who decides whether to retry or redeploy the previous release?
6. Should the previous successful app release be retained until a later release succeeds, so rollback is always available?
7. Who receives operational/security alerts, and what response time is expected for the current internal apps?
8. Which OS/provider combinations and cost constraints must be supported initially? Is provider neutrality a first-release requirement or a later goal?
9. Which host lifecycle actions are in scope: registration, replacement, retirement, access revocation, and secure removal of data?

## Context

Based on `docs/requirements/01/requirements_v1.md` and compared with `docs/notes/vps-bootstrap-plan.md`. The bootstrap plan's conservative exclusions are planning assumptions to reconcile, not automatically settled product requirements. This note records the brainstorm and does not modify the original requirements or select implementation details.
