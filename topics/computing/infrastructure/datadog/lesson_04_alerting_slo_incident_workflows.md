# Lesson 4: Alerting, SLO, Incident Workflows

## 1. First-Principles Intuition & Invariants

Every monitoring system is, at its core, a decision engine. It consumes a stream of observations about a running system, evaluates those observations against expected behavior, and either concludes that nothing demands human attention or fires a signal that initiates a response. The apparent simplicity of this formulation hides an enormous amount of engineering complexity, because the quality of the decision engine determines whether your on-call rotation is a team of skilled engineers exercising informed judgment or an exhausted group of people reflexively silencing alarms at 3 AM.

The foundational tension in alerting is the tradeoff between sensitivity and specificity, terms borrowed from signal detection theory. A perfectly sensitive alerting system fires every time a real problem occurs; a perfectly specific one never fires when no real problem exists. These two properties are in direct conflict, and every threshold you configure, every evaluation window you choose, and every anomaly detection algorithm you deploy represents a deliberate position on this tradeoff surface. Setting your CPU utilization alert at 60% yields high sensitivity but terrible specificity: you get paged for workloads whose normal operating range routinely touches 70%. Setting it at 99% flips the problem. The engineering challenge is that "real problem" is not a fixed definition — it depends on the semantics of the service, the load pattern, the time of day, and what your users are actually experiencing.

Datadog's alerting model is built on the concept of **monitor evaluation**, which is the process of periodically computing a scalar summary of a time-series query and comparing that scalar against a threshold or statistical model. Understanding exactly what "periodically" and "scalar summary" mean in practice is not academic: these definitions determine the guarantee your alerting system provides.

Datadog evaluates most monitors on a 60-second cycle. Each evaluation retrieves the metric time-series for the configured query window, applies an aggregation function — typically `avg()`, `max()`, `min()`, or `sum()` — across that window, and produces a single scalar. That scalar is then tested against the alert and warning thresholds. The implication is that your alert does not fire the instant a metric crosses a threshold; it fires at the next evaluation tick after the aggregated value crosses it. For a 5-minute query window evaluated every 60 seconds, a spike that lasts 90 seconds may not register as a threshold crossing at all if it falls between two evaluation windows in an unfortunate way. This is the aliasing problem, and it means you must think carefully about the relationship between the duration of the fault you are trying to detect and the duration of your evaluation window.

The evaluation window and the query window are distinct but related concepts. The **query window** is the span of time over which metric data is fetched and aggregated; the **evaluation window** is the sliding or tumbling frame within which Datadog looks for data to decide whether the monitor is in alert, warn, OK, or No Data state. When you configure a monitor to alert if the average latency over the last 10 minutes exceeds 500 ms, those 10 minutes are the query window. The monitor enters ALERT state only when that 10-minute rolling average persistently exceeds the threshold at an evaluation tick, not when any individual sample does. This windowed aggregation is a deliberate low-pass filter: it suppresses transient spikes and reduces false positives, but it also increases detection latency for sustained faults.

This introduces a fundamental invariant that all production alerting should respect: **detection latency is proportional to the evaluation window**. If you need to detect and respond to a 2-minute outage, your evaluation window must be shorter than 2 minutes, ideally closer to 30 seconds with a narrow query window and high-frequency metrics ingestion. If your SLA tolerates a 15-minute degradation before action is required, a 10-minute window is perfectly appropriate. Aligning your evaluation window to your acceptable time-to-detect is one of the most consequential configuration decisions in an alerting system, and it is one that most teams set once during initial setup and never revisit.

The second foundational invariant is that **alerts measure symptoms, not causes**. A CPU utilization spike is not a problem in itself; it is a signal that may or may not indicate that users are experiencing elevated latency. The highest-value alerts are those closest to user experience: error rate, latency at a given percentile, and availability. Alerts on internal resource metrics like CPU, memory, and disk I/O are useful for capacity planning and debugging, but they should rarely wake someone up at night unless they are directly correlated with user-visible degradation. This philosophy, articulated clearly in Google's Site Reliability Engineering book, is the theoretical backbone behind Service Level Objectives — the formalization of alerting on what actually matters to users rather than on the internal machinery that serves them.

---

## 2. Core Architecture & Mechanics

### Monitor Evaluation Semantics and the State Machine

A Datadog monitor is a persistent object in the Datadog control plane that runs a parameterized query on a periodic schedule and transitions through a defined set of states based on evaluation results. Understanding the state machine precisely is prerequisite to building reliable alerting workflows, because notification routing, escalation policies, and incident creation are all triggered by specific state transitions, not by states themselves.

The monitor state machine has four primary states and several composite states for multi-alert monitors:

```
                   ┌─────────────────────────────────────────────────────────┐
                   │                  MONITOR STATE MACHINE                  │
                   └─────────────────────────────────────────────────────────┘

         ┌──────────┐   threshold      ┌───────────┐   threshold    ┌───────────┐
         │          │   exceeded       │           │   exceeded     │           │
         │    OK    │ ─────────────► │   WARN    │ ───────────► │   ALERT   │
         │          │                 │           │               │           │
         └──────────┘ ◄───────────── └───────────┘ ◄──────────── └───────────┘
              ▲        below warn                   below alert          │
              │                                                          │
              │             recovery threshold met                       │
              └──────────────────────────────────────────────────────────┘

         ┌──────────────┐
         │   NO DATA    │  ◄── query window returns no metric samples
         └──────────────┘
                │
                ▼
        notify or ignore
        (configured per monitor)
```

The transition from OK to WARN to ALERT is intuitive, but the recovery transition is where most practitioners make errors. By default, a monitor recovers from ALERT back to OK when the metric drops below the alert threshold. This means that for a threshold of 500 ms, a monitor oscillates between ALERT and OK if the metric fluctuates around 490–510 ms, producing alert flapping. Datadog's **recovery threshold** parameter addresses this directly: you can configure a separate, lower value that the metric must fall below before the monitor transitions out of ALERT. If your alert threshold is 500 ms and your recovery threshold is 400 ms, the monitor will not recover until the metric sustainably falls 100 ms below the trigger point, introducing hysteresis into the state machine. This is the alerting equivalent of a Schmitt trigger in electronics: the asymmetric switching thresholds eliminate oscillation around a single boundary.

The `require_full_window` parameter is another critical piece of evaluation semantics. When set to `true` (the default for most metric monitors), Datadog refuses to evaluate the monitor if the query window does not contain a sufficient density of data points. If you have a 10-minute query window and metric collection is interrupted for 8 of those 10 minutes, the monitor will not fire even if the available data exceeds the threshold. This prevents false positives during sparse data collection, but it also means that a monitor configured this way is blind to the first several minutes of a new host's life. For services that scale down to zero, this can produce a gap in alert coverage during scale-up.

**Multi-alert monitors** decompose a single monitor definition across multiple tag values, creating one evaluation context per unique tag combination. When you configure a monitor with `avg:trace.web.request.duration{env:prod} by {service}`, Datadog creates a sub-monitor for every distinct service tag value it has seen in the last query window. Each sub-monitor maintains its own independent state machine. The parent monitor is in ALERT if any sub-monitor is in ALERT. This architecture means that a single monitor definition can generate 50 simultaneous alert notifications if 50 services cross the threshold simultaneously — a scenario that is simultaneously informationally correct and operationally catastrophic if your incident workflow is not designed to handle group alerting with de-duplication.

### Composite Monitors and Boolean Condition Graphs

A composite monitor evaluates a boolean expression over the states of two or more existing monitors. Rather than writing a single complex query that attempts to capture multi-dimensional fault conditions, you compose independent monitors and define the logical relationship between their states.

```hcl
# Terraform definition of a composite monitor
resource "datadog_monitor" "api_degradation_composite" {
  name    = "API Degradation: High Latency AND Elevated Error Rate"
  type    = "composite"
  message = <<-EOT
    API gateway is experiencing simultaneous latency and error rate elevation.
    This composite condition indicates load shedding or upstream dependency failure.
    Runbook: https://wiki.internal/runbooks/api-degradation
    @pagerduty-api-oncall
  EOT

  query = "${datadog_monitor.api_p99_latency.id} && ${datadog_monitor.api_error_rate.id}"

  tags = ["env:prod", "team:platform", "service:api-gateway"]
}
```

The composite monitor evaluates `&&`, `||`, and `!` operators over the states of the referenced monitors. ALERT is treated as `true` and OK as `false` for boolean evaluation purposes. WARN is treated as `false` by default, though you can configure the composite to treat WARN as `true` by using the `WARN_OR_ALERT` macro in the query.

The power of composite monitors is that they let you model multi-causal fault conditions precisely. A single high-latency event might be a momentary GC pause; simultaneous high latency and an elevated connection pool wait time is almost certainly a database saturation event. The composite condition encodes this domain knowledge into the alerting topology itself rather than relying on the on-call engineer to reason about it at 2 AM.

The important caveat is that composite monitors are only as reliable as their constituent monitors' data freshness. If sub-monitor A evaluated 55 seconds ago and sub-monitor B evaluated 5 seconds ago, the composite evaluation is using states computed at different points in time. For slowly-evolving conditions this is harmless; for rapid fault progressions, the temporal misalignment can produce false composite states. In practice, this is rarely a production problem, but it is worth understanding when you are building composite monitors for time-sensitive SLA breach conditions.

### Anomaly Detection: Statistical Models and Their Failure Modes

Threshold-based alerting requires you to know in advance what "bad" looks like in terms of raw metric values. For many production metrics — particularly those exhibiting strong seasonal patterns, long-term growth trends, or complex multi-modal distributions — specifying a fixed threshold is impractical. A web service's request rate at 9 AM on a Monday is structurally different from its request rate at 3 AM on a Sunday. Alerting on absolute values requires you to either set the threshold high enough to avoid weekend false positives (at the cost of missing weekday incidents) or low enough to catch weekday incidents (at the cost of constant weekend noise).

Datadog's anomaly detection addresses this by replacing the fixed threshold with a dynamically computed expected range. The monitor alerts when the metric falls outside a band defined as the expected value plus or minus some number of standard deviations, where "expected" is estimated by one of three algorithms.

The **Basic** algorithm is a rolling statistical model: it computes the mean and standard deviation of the metric over a trailing window (typically 2 hours) and defines the anomaly band as mean ± (N × stddev). This model has no concept of seasonality and will misclassify the daily peak as an anomaly if the lookback window does not cover the previous peak. It is appropriate for metrics that are stationary: metrics that fluctuate around a stable mean without systematic time-of-day or day-of-week patterns.

The **Agile** algorithm uses SARIMA — Seasonal AutoRegressive Integrated Moving Average — a classical time-series forecasting model that explicitly models seasonal periodicity. Datadog's implementation fits a SARIMA model with a weekly seasonal period (10,080 minutes) and a daily seasonal period (1,440 minutes). This means the model needs several weeks of historical data to fully capture the seasonal components. When you deploy an anomaly monitor on a new service, the model is operating on incomplete historical data and will produce wider, less specific confidence bands until it has accumulated sufficient history. The agile algorithm is appropriate for metrics with predictable weekly and daily patterns, such as request rates, active user counts, and business transaction volumes.

The **Robust** algorithm is designed for metrics that change slowly over time, such as a system whose baseline grows week over week due to organic load growth. It uses a decomposition approach that separates the trend component from the seasonal and residual components, allowing the model to alert on deviations from the current trend level rather than from a historical absolute value. If your service's p99 latency has been slowly increasing over three months, the agile model will eventually treat elevated latency as normal and stop alerting; the robust model continues to alert if the rate of change itself accelerates beyond what the trend predicts.

```python
# Datadog anomaly monitor query syntax
# Alerts when the metric deviates from the agile seasonal model
# by more than 2 standard deviations for 80% of a 15-minute window

avg(last_15m):anomalies(
  avg:trace.web.request.duration.by.service{env:prod,service:checkout},
  'agile',
  2,
  direction='above',
  interval=60,
  alert_window='last_15m',
  count_default_zero='true'
) >= 0.8
```

The `>= 0.8` threshold means the monitor enters ALERT when the metric exceeds the upper anomaly band for at least 80% of the evaluation window's data points. This percentage threshold is itself a sensitivity control: at `>= 1.0`, a single point inside the band during the window prevents the alert from firing; at `>= 0.1`, almost any anomalous point triggers it. Setting this between 0.6 and 0.8 provides a practical balance between catching sustained anomalies and suppressing transient outliers.

The critical failure mode of anomaly detection is **training data contamination**. If the metric was anomalous during the period that the model uses for training, the model learns the anomalous behavior as normal and produces an artificially wide or miscentered confidence band. After a major incident, Datadog allows you to specify training data exclusion windows precisely to avoid this. If your service experienced a 4-hour outage last Tuesday, you should configure the anomaly monitor to exclude that window from the SARIMA model's training set, otherwise the model will treat elevated error rates during Tuesday afternoons as seasonally normal.

### SLO Architecture: Error Budgets and Burn Rate Mathematics

A Service Level Objective is a formal contract between a service and its consumers that specifies the minimum acceptable level of reliability over a rolling time window. In Datadog's implementation, SLOs are first-class objects with their own persistence, budget tracking, and alerting primitives. Understanding their internal mechanics requires working through the mathematics before examining the configuration.

An SLO defines a **target** — say, 99.9% availability — over a **window** — typically 30 days. The error budget is the complement of the target expressed as a fraction of the window:

$$\text{Error Budget} = (1 - \text{Target}) \times \text{Window Duration}$$

For a 99.9% target over a 30-day window:

$$\text{Error Budget} = (1 - 0.999) \times 30 \times 24 \times 60 = 43.2 \text{ minutes}$$

This means your service can be unavailable for up to 43.2 minutes in any rolling 30-day period without breaching the SLO. The error budget is the operational slack that engineering teams spend on deployments, maintenance windows, and experimentation. When the budget is depleted, further feature work that risks reliability should stop until the budget replenishes through elapsed time.

Datadog tracks two types of SLOs with different underlying data sources. A **Metric-based SLO** is defined by a good/total request ratio query:

```
SLI = sum:trace.web.request.hits{env:prod,service:api,http.status_code:2xx}.as_count()
    / sum:trace.web.request.hits{env:prod,service:api}.as_count()
```

This measures availability as the fraction of successful requests. A **Monitor-based SLO** is defined by the uptime fraction of an existing monitor: the SLO is "good" during windows when the monitor is in OK state and "bad" during windows when it is in ALERT state. Metric-based SLOs provide finer-grained accounting because they track success at the individual request level; monitor-based SLOs are coarser because a monitor that fires for 5 minutes counts all requests during those 5 minutes as failures regardless of whether the monitor alarm actually correlated with request-level failures.

Burn rate alerting extends SLO monitoring from passive budget tracking to active alerting. The **burn rate** is the ratio of the current error rate to the error rate that would exactly exhaust the budget at the end of the window:

$$\text{Burn Rate} = \frac{\text{Current Error Rate}}{\text{Budget Error Rate}}$$

A burn rate of 1.0 means you are consuming errors at exactly the pace that will exhaust the budget at the end of the window. A burn rate of 10 means you are consuming budget 10 times faster than sustainable: at this rate, a 30-day budget is exhausted in 3 days. The significance of burn rate alerting is that it converts the abstract notion of "budget remaining" into an immediately actionable time-to-exhaustion figure.

Google's SRE workbook establishes a multi-window, multi-burn-rate alerting scheme that Datadog's SLO alerting directly implements. The scheme uses two burn rate thresholds evaluated over two different time windows simultaneously:

```
┌─────────────────────────────────────────────────────────────────────┐
│          MULTI-WINDOW BURN RATE ALERT CONFIGURATION                 │
│                        (99.9% SLO, 30-day window)                   │
├──────────────────┬─────────────┬─────────────┬──────────────────────┤
│ Severity         │ Burn Rate   │ Short Window│ Long Window          │
├──────────────────┼─────────────┼─────────────┼──────────────────────┤
│ P1 - Critical    │    14.4x    │   5 min     │ 1 hour               │
│ P2 - High        │     6.0x    │  30 min     │ 6 hours              │
│ P3 - Warning     │     3.0x    │  2 hours    │ 1 day                │
└──────────────────┴─────────────┴─────────────┴──────────────────────┘
```

The 14.4x burn rate threshold at the critical severity level has a specific mathematical meaning: at a 14.4x burn rate, a 30-day budget is exhausted in approximately 50 hours. The alert fires only when both the short window (5 minutes) and the long window (1 hour) independently confirm the burn rate, requiring that both the recent signal and the sustained trend are anomalous. This two-window confirmation is the mechanism that eliminates false positives from brief traffic spikes: a spike lasting 10 minutes will trigger the 5-minute window but not the 1-hour window, so the alert does not fire.

Datadog's SLO alert configuration expresses this directly in the Terraform provider:

```hcl
resource "datadog_slo_alert" "api_burn_rate_critical" {
  name         = "API Gateway SLO: Critical Burn Rate (14.4x)"
  slo_id       = datadog_service_level_objective.api_availability.id
  type         = "burn_rate"
  target       = 99.9
  timeframe    = "30d"

  slo_alert_query = {
    burn_rate_threshold = 14.4
  }

  evaluation_window = {
    short_window = "5m"
    long_window  = "1h"
  }

  message  = <<-EOT
    **CRITICAL: API Gateway error budget is burning at 14.4x sustainable rate.**
    At this rate, the 30-day error budget will be exhausted in under 50 hours.
    Current error rate: {{value}}%
    Error budget remaining: {{slo_error_budget_remaining}}%
    Runbook: https://wiki.internal/runbooks/api-slo-breach
    @pagerduty-api-oncall @slack-incidents-prod
  EOT

  tags = ["env:prod", "service:api-gateway", "team:platform", "severity:critical"]
}
```

The variable `{{slo_error_budget_remaining}}` in the message template expands to the current error budget percentage at the time of notification. Including this in the notification body immediately communicates the operational context to the on-call engineer without requiring them to open the Datadog UI before deciding how urgently to respond.

### Notification Routing and the Signal Delivery Pipeline

When a monitor transitions into ALERT state, Datadog must decide where to route the notification. This routing is not configured in a central policy file; it is embedded directly in the monitor's message field using `@mention` syntax. This design collocates the routing definition with the monitor definition, which simplifies auditing (every monitor's notification target is visible inline) but can produce routing inconsistencies across a large monitor estate if not managed through infrastructure-as-code.

The `@pagerduty-{service-name}` mention triggers an event in PagerDuty that creates an incident and applies that service's escalation policy. The `@slack-{channel-name}` mention posts a formatted notification card to the specified Slack channel. Datadog supports over 450 integrations, but the operational ones — PagerDuty, Opsgenie, Slack, Microsoft Teams, and VictorOps — all follow the same pattern: the mention is a signal that Datadog POSTs to the integration's inbound webhook or API endpoint.

The critical operational detail is that Datadog resolves `@mention` routing at notification time by evaluating conditional blocks inside the monitor message:

```
{{#is_alert}}
  @pagerduty-api-oncall
  @slack-incidents-prod
{{/is_alert}}

{{#is_warning}}
  @slack-platform-warnings
{{/is_warning}}

{{#is_recovery}}
  @pagerduty-api-oncall
  @slack-incidents-prod
  Incident auto-resolved. Verify service health in dashboard: {{link}}
{{/is_recovery}}

{{#is_no_data}}
  @slack-platform-warnings
  Metric data gap detected. Check collection health.
{{/is_no_data}}
```

This template system lets you route ALERT transitions to PagerDuty (which wakes someone up) while routing WARN transitions to a Slack channel (which provides ambient awareness without interruption). Recovery notifications go back to PagerDuty to auto-resolve the open incident, closing the loop without manual intervention.

---

## 3. High-Performance Optimization & Failure Modes

### Monitor Evaluation at Scale: Cardinality and Query Cost

The practical scalability limit of Datadog's alerting infrastructure is not the number of monitors but the **cardinality of the by-clause in multi-alert monitors**. Each unique tag value combination in the `by {}` clause creates an independent evaluation context. A monitor scoped `by {service, host}` across 50 services and 200 hosts produces up to 10,000 evaluation contexts. Each context must have its query evaluated, its state machine transitioned, and its notification eligibility checked on every 60-second evaluation cycle. At scale, this produces significant query processing load in Datadog's metrics store and can delay evaluation cycles under heavy load, introducing detection latency that is not attributable to your query window configuration.

The mitigation is to design multi-alert monitors with the minimum cardinality sufficient to serve your incident routing needs. If you need per-service alerting, use `by {service}` and not `by {service, host, availability_zone, pod_name}`. The more granular dimensions can always be added to the alert notification as template variables that resolve to the top-offending value at notification time:

```
# In the monitor query:
avg:trace.web.request.duration{env:prod} by {service}

# In the monitor message, resolve contributing dimensions:
Service {{service.name}} p99 latency is {{value}}ms
Top contributing host: {{host.name}}
```

This decouples the evaluation cardinality (one context per service) from the diagnostic richness of the notification (which can include host-level breakdown via the linked dashboard).

### Flap Detection and Notification Suppression

Alert flapping — where a monitor oscillates between ALERT and OK states repeatedly over a short period — produces notification floods that rapidly train engineers to ignore all alerts. Flapping is the principal cause of alert fatigue in production environments, and it is predominantly caused by metrics that hover near a threshold rather than by fundamentally pathological thresholds.

Datadog's renotification interval controls how frequently a monitor that remains in ALERT state re-sends notifications. Setting this to `no renotification` means you receive one ALERT notification and then silence until recovery; setting it to `every 30 minutes` re-pages the on-call if the condition persists. The correct choice depends on your incident workflow: if PagerDuty's escalation policy handles escalation automatically, renotification is redundant and noisy. If your incident workflow depends on humans manually escalating after a certain dwell time, renotification provides the trigger.

The recovery threshold discussed in section 2 is the first line of defense against flapping. The second is the `evaluation_delay` parameter, which introduces a fixed offset between the current time and the most recent data point considered in the evaluation window. This is particularly valuable for metrics ingested through Lambda functions or Kubernetes pods with variable reporting latency: a 60-second evaluation delay ensures that the evaluation window never includes the final 60 seconds of data, which may not yet be fully populated due to in-flight telemetry. The result is a slight increase in detection latency in exchange for significant reduction in false positives from partially-populated windows.

### Incident State Machine and Lifecycle Management

Datadog Incident Management models an incident as an explicit state machine with defined transitions, properties, and integration hooks. An incident transitions through the following lifecycle:

```
                ┌────────────────────────────────────────────────────────────┐
                │                   INCIDENT LIFECYCLE                       │
                └────────────────────────────────────────────────────────────┘

   Alert fires          Engineer declares    Root cause      Post-mortem
   in Datadog           incident             identified      complete
       │                     │                   │               │
       ▼                     ▼                   ▼               ▼
  ┌─────────┐          ┌──────────┐         ┌────────┐     ┌──────────┐
  │TRIGGERED│─────────►│  ACTIVE  │────────►│STABLE  │────►│ RESOLVED │
  └─────────┘  declare └──────────┘ stabilize└────────┘     └──────────┘
                            │                                     ▲
                            │         ◄── auto-resolve ───────────┘
                            │         if monitor recovers
                            │         and no manual override
                            ▼
                    ┌──────────────────┐
                    │ Timeline entries │
                    │ Responder roster │
                    │ Linked monitors  │
                    │ Linked dashboards│
                    └──────────────────┘
```

An incident in Datadog carries several fields that are set at creation time or updated as the investigation progresses: severity (SEV1 through SEV5), customer impact statement, incident commander, affected services, and a live timeline. The timeline is the operational record of the incident: every monitor transition, every comment left by a responder, every command output pasted into the timeline becomes a timestamped entry that feeds the post-mortem process. Teams that treat the timeline as a first-class artifact during the incident produce significantly better post-mortems because they are not reconstructing a sequence of events from memory and log timestamps.

Incidents can be declared programmatically via the Datadog API or automatically triggered by monitor state transitions when the monitor's escalation settings are configured to create incidents on ALERT. The Terraform configuration for automatic incident creation links directly to the monitor definition:

```hcl
resource "datadog_monitor" "api_p99_latency" {
  name  = "API Gateway: p99 Latency SLO Threat"
  type  = "metric alert"
  query = "avg(last_5m):avg:trace.web.request.duration.by.service{env:prod,service:api-gateway}.rollup(avg, 60) > 0.5"

  message = <<-EOT
    API Gateway p99 latency has exceeded 500ms for 5 consecutive minutes.
    This is an SLO-threatening event. Declare a SEV2 incident immediately.
    @pagerduty-api-oncall
    @incident-sev2
  EOT

  monitor_thresholds {
    critical = 0.5
    warning  = 0.35
    critical_recovery = 0.4
    warning_recovery  = 0.3
  }

  notify_no_data    = true
  no_data_timeframe = 10
  renotify_interval = 30
  require_full_window = false
  evaluation_delay    = 60

  tags = ["env:prod", "service:api-gateway", "team:platform", "slo:api-availability"]
}
```

The `@incident-sev2` mention triggers Datadog's incident automation to create a SEV2 incident, populate it with the monitor context, and invoke any configured incident workflow automations — which can include Slack channel creation, PagerDuty incident creation with the correct service and urgency, Jira ticket creation, and status page update via Statuspage.io.

### Escalation Policies and On-Call Rotation Integration

Escalation policies answer the question of what happens when the first responder does not acknowledge a page within a specified timeout. Datadog Incident Management has a native on-call scheduling feature introduced with Datadog On-Call, but the majority of production deployments still route pages to PagerDuty or Opsgenie and rely on those platforms' escalation policy engines, which have more mature rotation management, override capabilities, and historical analytics.

The critical integration point is the monitor's recovery notification. When a monitor recovers, Datadog must send a resolution signal back to PagerDuty to auto-resolve the open incident. Without this, PagerDuty's incident list accumulates stale open incidents, and the signal-to-noise ratio of the incident dashboard degrades until it is useless. The resolution signal flows through the same `@pagerduty-{service-name}` mention in the monitor's recovery message template, and PagerDuty matches it to the open incident using the monitor's globally unique identifier, which Datadog includes as the `dedup_key` in the PagerDuty Events API v2 payload.

The `dedup_key` is worth understanding in depth because it governs whether Datadog creates a new PagerDuty incident or updates an existing one. For single-alert monitors, the `dedup_key` is the monitor ID. For multi-alert monitors, it is the monitor ID concatenated with the specific tag value combination of the triggering sub-monitor. This means that if your `by {service}` monitor fires for `checkout` and `payments` simultaneously, PagerDuty receives two distinct events with two distinct `dedup_key` values and creates two separate incidents. Whether this is the desired behavior depends on your incident management philosophy: separate incidents enable separate responder assignments and separate post-mortems, but they may represent what is operationally a single correlated event.

The resolution to correlated multi-service incidents is typically handled at the PagerDuty layer using **alert grouping**, which bundles multiple related incidents into a single parent incident based on title similarity, service tags, or time proximity. Configuring alert grouping in PagerDuty rather than trying to collapse the signal in Datadog keeps the monitoring layer and the incident management layer concerns correctly separated: Datadog's job is to detect and report precisely what it observes; PagerDuty's job is to route and correlate that signal for human response.

### Operational Anti-Patterns and Their Mitigations

The most common failure mode in production alerting estates is **monitor debt**: the accumulation of monitors that no one maintains, whose thresholds are no longer calibrated to current service behavior, and whose notification targets point to Slack channels or PagerDuty services that no longer reflect actual team ownership. Monitor debt compounds over time because every false positive reduces the team's trust in the alerting system, which causes them to ignore pages rather than investigate them, which allows real incidents to go undetected.

The mitigation requires treating monitors as production code: every monitor must have an owner tag, a runbook link, and a threshold that is periodically reviewed against actual alert frequency data. Datadog's `avg_over_dt` function and the Monitors Quality tool (available in the Datadog UI under Monitors → Quality) can identify monitors that have never fired, monitors that fire more than a configurable frequency threshold, and monitors with no runbook configured.

The second anti-pattern is **alert-to-ticket coupling**: creating a Jira ticket for every alert that fires. This produces ticket volumes that overwhelm the team's ability to triage, causing the ticketing system to become a graveyard of unresolved low-priority alerts rather than a managed queue of actionable work. The correct coupling point between alerting and ticketing is not the monitor alert transition but the incident declaration. Incidents that are declared (representing genuine service-impacting events) should produce tickets; alert state transitions that do not meet the incident declaration threshold should produce only Slack notifications for ambient awareness.

The third anti-pattern is neglecting the `No Data` state. A monitor in No Data state is indistinguishable from a monitor that has stopped functioning. If your metrics collection pipeline fails — a Datadog Agent that crashes, a DaemonSet that fails to restart after a node drain, or a firewall rule that blocks outbound metrics traffic — every monitor that depends on that collection path silently enters No Data and stops providing any signal. The correct configuration is `notify_no_data = true` with a `no_data_timeframe` set to approximately three times your collection interval: if you collect metrics every 60 seconds, alert on no data after 3 minutes. This ensures that collection failures are themselves detected and routed to the platform team, maintaining the integrity of the monitoring system's monitoring of itself.
