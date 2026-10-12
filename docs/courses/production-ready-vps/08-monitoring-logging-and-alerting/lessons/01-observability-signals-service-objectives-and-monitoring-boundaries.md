# 01 — Observability signals, service objectives, and monitoring boundaries

## Learning objectives

You can describe the difference between monitoring and observability, select signals that answer operational questions, turn user expectations into measurable objectives, and identify where monitoring itself can fail.

## Begin with questions, not products

Monitoring gathers and evaluates signals over time to determine whether a known condition is healthy or needs attention. Observability is the ability to infer the system's internal state from the evidence it emits. A dashboard is only a presentation; it does not make an unknown failure understandable. A useful design begins with questions:

- Can a user reach the intended application over the public domain and HTTPS?
- Is the application able to serve its important operations, not just accept a TCP connection?
- Is the VPS approaching a CPU, memory, disk-space, inode, or network limit?
- Did a deploy, restart, dependency failure, or configuration change coincide with the symptom?
- If the signal source or alert route fails, will anyone know?

No single signal answers all of these. Use a small set of complementary signal types:

| Signal | Best for | Typical limitations |
|---|---|---|
| Metrics | Trends, rates, saturation, thresholds, and comparisons over time | Aggregation can hide individual events; labels can create high cardinality |
| Logs | Specific events, errors, context, and diagnostic details | Volume can grow quickly; unstructured or sensitive logs are difficult and unsafe to search |
| Health checks / synthetic probes | User-visible availability and a defined operation | A shallow check can pass while important functions fail; probes add load |
| Alerts | Directing attention to a condition that requires action | Poorly tuned rules create fatigue; an untested route may silently fail |

Traces can help follow a request through multiple services, but a single-VPS application should add them when the architecture and diagnostic need justify their complexity. Do not deploy a large telemetry stack merely to collect every possible signal. Start with host resource telemetry, application-specific health, bounded logs, an external availability probe, and alerts for conditions that require a human.

## Define service-level indicators and objectives

A **service-level indicator (SLI)** is a measured expression of service behavior, such as successful valid requests divided by all eligible requests, or the fraction of requests completed under a latency target. A **service-level objective (SLO)** is an agreed target for an SLI over a stated time window. A **service-level agreement (SLA)** is an external commitment with consequences; do not call an internal target an SLA unless one actually exists.

Define the measurement before choosing its threshold. For availability, specify what counts as a valid check, its location, cadence, expected status/body or operation, treatment of planned maintenance, and the reporting window. A TCP port-open test is not equivalent to an application transaction. For latency, state whether the measure is end-user probe latency, server request latency, or another value and define a percentile or limit. Avoid targets unsupported by product expectations or historical evidence; establish a baseline, agree on a target with the service owner, and revise it only through a recorded decision.

An error budget is the portion of the SLO's allowed failure remaining in its window. It can help prioritize reliability work over risky changes, but it is useful only when the SLI is trustworthy and someone acts on the result. Small services may begin with a simple monthly availability objective and a short incident review rather than building a complex budget system.

Host symptoms are not themselves service objectives. High CPU may be harmless during a brief build; a full filesystem can be an imminent outage even if average CPU is low. Prefer alerts on user impact or sustained risk, and use host metrics to explain or predict that impact.

## Design a signal path with independent failure boundaries

Think through the complete path:

```text
Application / VPS
   | metrics, health, logs
   v
Collector or provider agent
   | transport and storage
   v
Dashboard and rule evaluator
   | notification integration
   v
Human responder

External probe ----------------------^
Independent source checks public behavior
```

If the collector, rule evaluator, and notifications all run on the monitored VPS, a host crash can remove both the service and its evidence of failure. A local agent can still collect useful host telemetry during normal operation, but add a provider-level monitor or an external uptime check and route critical alerts through an independently reachable service. Consider how loss of Internet access, credentials, DNS, or the notification provider affects this chain.

Each signal needs a source, timestamp, named owner for its source and collection path, useful retention period, and defined behavior when missing. Name the alert responder separately; on a small service, the same person may hold both roles. Stale data must not look like healthy zero. Alert on missing telemetry when its absence prevents a critical decision. Keep a deliberate list of blind spots: for example, an external check sees public behavior but cannot identify a disk bottleneck; host metrics can show disk pressure but cannot prove that a user can sign in.

## Keep the design proportionate to a single VPS

The monitoring stack consumes the same CPU, memory, disk, and network that the application needs. Estimate retention and resource usage before installing it. Prefer a managed/provider service or a lightweight agent when it meets the need; if you self-host a collector and dashboard, restrict access, cap retention, and understand the consequences of losing the host. Do not expose an exporter or metrics endpoint publicly simply to make collection convenient.

Before production changes, record a baseline with representative normal traffic and a controlled maintenance or deployment window. Label unusual expected work, such as backup or image builds. Baselines make thresholds meaningful, but avoid treating historical normal behavior as safe when it includes a known capacity issue.

## Practical checkpoint

Complete [Task 01 — Define service signals, ownership, and measurable objectives](../tasks/01-define-service-signals-ownership-and-measurable-objectives.md) before selecting monitoring rules or writing alert thresholds.

## Knowledge check

1. Why is a successful TCP connection not sufficient proof that a web application is available?
2. How does an SLI differ from an SLO and an SLA?
3. What can an external uptime probe tell you that a host agent cannot, and vice versa?
4. Why must missing or stale telemetry be distinguished from a zero value?

## References

- [Google SRE Book — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- [OpenTelemetry — Signals](https://opentelemetry.io/docs/concepts/signals/)
