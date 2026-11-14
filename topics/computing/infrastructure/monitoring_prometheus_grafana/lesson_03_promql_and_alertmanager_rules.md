# Lesson 3: PromQL Querying & Alertmanager Rule Engineering

## 1. Architectural Foundations & Invariants

### The Promise of PromQL: Time-Series Algebra at Scale

Prometheus does not store pre-computed dashboards or aggregated results. Every graph, every alert, every metric value you see is computed on-demand from raw time-series data through PromQL—a domain-specific query language built atop Prometheus's in-memory TSDB. Understanding PromQL is not optional for infrastructure teams; it is the bridge between raw observability data and actionable intelligence.

PromQL operates on an immutable, append-only time series model. Each series is identified uniquely by its metric name and label set. When you query `http_requests_total{job="api-server", instance="10.0.1.5:9090"}`, you are asking Prometheus to return all samples matching that exact combination of labels within the query range. This label-driven selectivity is fundamental to Prometheus's design: it prevents cardinality explosion by forcing explicit, intentional queries rather than supporting ad-hoc wildcard searches.

The language itself divides operations into four core categories: **instant vector queries** (point-in-time snapshots), **range vector queries** (time windows of samples), **scalar operations** (arithmetic and comparisons), and **aggregation functions** (combining multiple series into derived results). Each category has distinct semantics and performance implications that senior engineers must internalize.

### Invariant: Labels Are Dimensions, Not Values

A critical architectural principle often misunderstood: Prometheus labels are dimensions for slicing and dicing data, not storage for high-cardinality values. Using a label like `user_id` or `request_id` violates Prometheus's design contract and will cause out-of-memory crashes. Each unique label value creates a new time series, and at scale (thousands of servers, hundreds of applications), cardinality spirals out of control.

The safe cardinality ceiling for a single metric is typically 10,000 unique series, though mature deployments often operate in the 100,000–500,000 range across their entire Prometheus instance. Exceeding 1 million series requires purpose-built infrastructure and careful tuning.

### Invariant: Scrape Intervals Define Temporal Resolution

Prometheus scrapes metrics at intervals (default 15 seconds). Every PromQL query operates on this discrete, step-aligned timeline. When you query `rate(http_requests_total[5m])`, Prometheus returns one point per scrape interval, calculated from the 5-minute window ending at that scrape timestamp. This has profound implications: you cannot meaningfully query at finer granularity than your scrape interval, and range durations must be multiples of your scrape interval for reliable results.

---

## 2. Core Mechanics & Data Structures

### 2.1 Instant Vectors: Point-in-Time Snapshots

An instant vector is the most basic PromQL construct: a set of time series with a single sample value per series at a given timestamp. The query evaluates to "now" by default, but you can anchor it to a past moment using the `offset` modifier.

```promql
# Return the current value of http_requests_total for all series
http_requests_total

# Return the value as it was 5 minutes ago
http_requests_total offset 5m

# With label matching: exact equality
http_requests_total{job="api-server", instance="prod-api-01:9090"}

# Label regex matching
http_requests_total{job=~"api-.*", instance!~"staging.*"}

# All series with a label called 'region', regardless of value
http_requests_total{region=""}

# Negated regex: exclude staging regions
http_requests_total{region!~"staging|canary"}
```

The matcher language supports four operators:

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Exact label equality | `job="api"` |
| `!=` | Label inequality | `job!="test"` |
| `=~` | Regex match (anchored full string) | `region=~"us-(east\|west)"` |
| `!~` | Regex non-match | `region!~"staging.*"` |

Regex matching in Prometheus uses RE2 syntax and is fully anchored: `=~"api"` does not match `api-server`; you must write `=~"api.*"`. This is a common source of bugs. Every regex match is compiled at query time and applied to all label values, so complex regexes on high-cardinality labels will spike CPU usage.

**Practical rule:** Use exact equality whenever possible. Reserve regex for multi-tenant environments or when you genuinely need pattern matching across many jobs or instance names.

### 2.2 Range Vectors: Windows of Time

A range vector extends an instant vector query with a time window, returning all samples within that window for each matching series. Range vectors are raw building blocks; you cannot directly graph them or return them from a query. They exist to feed into aggregation functions like `rate()`, `increase()`, and `histogram_quantile()`.

```promql
# All samples from http_requests_total in the last 5 minutes
http_requests_total[5m]

# 1-hour window, evaluated 10 minutes in the past
http_requests_total[1h] offset 10m

# 30-second window (useful for high-frequency scrape intervals)
http_requests_total[30s]
```

Range vector syntax is identical to instant vectors, but enclosed in brackets with a duration. Valid durations include `s` (seconds), `m` (minutes), `h` (hours), `d` (days), `w` (weeks), and `y` (years).

When you execute a range vector query directly in Prometheus's HTTP API, you get an error because range vectors are not scalar-yielding. However, the graph UI and most monitoring tools will apply a default aggregation function (usually `rate()`) automatically.

### 2.3 Rate Calculation: The Heart of Monitoring

The distinction between `rate()` and `irate()` is one of the most consequential details in Prometheus monitoring. Both functions calculate the per-second change of a counter over a specified time window, but their semantics differ fundamentally.

#### rate(): Stability via Linear Regression

`rate()` performs linear regression across all samples in the window, then extrapolates to the full window duration. This approach is resilient to gaps and scrape failures: if one or two samples are missing, the regression line still estimates a reasonable rate based on surrounding data.

```promql
# Return the average per-second rate of requests over the last 5 minutes
rate(http_requests_total[5m])

# With label selection
rate(http_requests_total{job="api-server"}[5m])

# Nested within arithmetic
(rate(http_requests_total[5m]) - rate(http_requests_total_error[5m])) / rate(http_requests_total[5m])
```

When a counter resets (instance restart, counter rollover), Prometheus detects the discontinuity and treats it as an instantaneous jump of the absolute difference. So if `http_requests_total` goes from 1,000,000 to 50,000 (restart), `rate()` correctly computes the difference as 1,000,000 - 50,000 = 949,950 new requests.

#### irate(): Instant Rate, High Sensitivity

`irate()` uses only the last two data points in the window and computes the instantaneous rate between them. This is more responsive to recent spikes but extremely noisy and sensitive to scrape timing jitter.

```promql
# Instantaneous rate based on the last two scrapes
irate(http_requests_total[5m])
```

The trailing window (e.g., `[5m]`) in `irate()` is only used for finding data points; all samples outside the last two are ignored. This makes `irate()` inappropriate for graphing or alerting on production metrics. **Best practice: use `rate()` for everything except emergency dashboards where you need subsecond responsiveness.**

#### increase(): Total Growth Without Normalization

`increase()` returns the total growth of a counter over the range, not normalized to per-second. It is mathematically equivalent to `rate() * range_duration_in_seconds`.

```promql
# Total requests in the last 5 minutes (not per-second)
increase(http_requests_total[5m])

# Useful for counting discrete events in a window
increase(login_attempts_total[1h])
```

### 2.4 Aggregation Operators: Combining Series

Prometheus provides a set of aggregation operators that combine multiple instant vectors into fewer results. These are the workhorses of monitoring queries.

#### sum, min, max, avg

The most common aggregations collapse all matching series into a single value:

```promql
# Total requests across all instances
sum(http_requests_total)

# Maximum memory usage across any instance
max(node_memory_MemFree_bytes)

# Average response time across instances
avg(http_request_duration_seconds)

# Minimum free disk space
min(node_filesystem_avail_bytes)
```

#### sum by, avg by, max by, min by: Aggregation with Dimensional Breakdown

The `by` modifier lets you aggregate while preserving specific label dimensions:

```promql
# Sum requests per job (all other labels discarded)
sum by (job) (http_requests_total)

# Average latency per endpoint and status code
avg by (endpoint, status_code) (http_request_duration_seconds)

# Max memory per region, keeping instance names
max by (region, instance) (node_memory_MemFree_bytes)

# Sum with multiple dimensions
sum by (job, instance) (rate(http_requests_total[5m]))
```

When you specify `by (label1, label2)`, the result contains only those labels. All other labels from the input are discarded. This is distinct from `without`:

#### without: Inverse Aggregation

`without` removes specific labels and aggregates the rest:

```promql
# Sum all requests except by instance (same as sum by job, region, ...)
sum without (instance) (http_requests_total)

# Useful when you know which labels to ignore rather than which to keep
avg without (endpoint) (http_request_duration_seconds)
```

Use `by` when you have a short list of desired dimensions; use `without` when you want to exclude a single dimension from a high-dimensional metric.

#### count, count_values, group

Counting and grouping operations:

```promql
# How many instances are exporting http_requests_total?
count(http_requests_total)

# How many instances per region?
count by (region) (up{job="prometheus"})

# Count instances by value (useful for checking version diversity)
count_values by (job) (prometheus_build_info{branch="main"})

# Group multiple inputs with no aggregation (rarely used)
group by (job) (http_requests_total)
```

#### topk, bottomk: N-Largest/Smallest

Select the top or bottom K series by value:

```promql
# Top 5 instances by request rate
topk(5, rate(http_requests_total[5m]))

# Bottom 3 instances (lowest memory usage)
bottomk(3, node_memory_MemFree_bytes)

# Top 10 endpoints by error count with label preservation
topk(10, sum by (endpoint) (rate(http_requests_total{status=~"5.."}[5m])))
```

`topk` and `bottomk` are computed at query time and can be expensive on high-cardinality metrics. Prefer pre-computed recording rules for frequently accessed top-K queries.

### 2.5 Histogram Quantiles: Latency Percentiles

Prometheus represents histograms as a set of counter metrics with the `_bucket`, `_count`, and `_sum` suffixes. Each bucket is a cumulative counter of observations less than or equal to its boundary.

```
# Raw histogram metrics for HTTP request duration
http_request_duration_seconds_bucket{le="0.005"}     = 100
http_request_duration_seconds_bucket{le="0.01"}      = 200
http_request_duration_seconds_bucket{le="0.025"}     = 350
http_request_duration_seconds_bucket{le="0.05"}      = 500
http_request_duration_seconds_bucket{le="0.1"}       = 600
http_request_duration_seconds_bucket{le="0.25"}      = 700
http_request_duration_seconds_bucket{le="0.5"}       = 750
http_request_duration_seconds_bucket{le="1.0"}       = 800
http_request_duration_seconds_bucket{le="+Inf"}      = 850
http_request_duration_seconds_count = 850
http_request_duration_seconds_sum = 123.45
```

The `histogram_quantile()` function performs linear interpolation across buckets to estimate the given quantile:

```promql
# 95th percentile (0.95 quantile) latency
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# 99th percentile per endpoint
histogram_quantile(0.99, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))

# 50th percentile (median)
histogram_quantile(0.5, http_request_duration_seconds_bucket)
```

**Critical detail:** You must aggregate buckets using `sum by (le, ...)` before calling `histogram_quantile()`. The `le` label is special—it represents the bucket boundary—and must be preserved. Omitting it or including other labels will produce incorrect results.

```promql
# CORRECT: aggregate rates by endpoint, preserving le
histogram_quantile(0.95,
  sum by (le, endpoint) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)

# WRONG: aggregating over le will destroy quantile calculation
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m]))
)
```

When interpolating between buckets, `histogram_quantile()` assumes a uniform distribution within each bucket. This is a reasonable approximation for most use cases but breaks down at extreme quantiles (p99.9, p99.99) where bucket granularity matters immensely. For applications requiring extremely precise tail latency measurements, use custom histograms with narrower bucket boundaries.

### 2.6 Binary Operators: Arithmetic and Comparisons

PromQL supports standard arithmetic and comparison operators that work on instant vectors. When operating on two vectors, Prometheus performs one-to-one matching based on label sets.

```promql
# Subtraction: error rate as a fraction
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Addition: total CPU time
node_cpu_seconds_total{mode="user"} + node_cpu_seconds_total{mode="system"}

# Comparison: flag instances using more than 80% memory
node_memory_MemFree_bytes / node_memory_MemTotal_bytes < 0.2

# Boolean result (1 if true, 0 if false)
rate(http_requests_total[5m]) > 1000
```

#### Vector Matching: One-to-One, Many-to-One, Many-to-Many

By default, binary operators use one-to-one matching: series are paired if their label sets are identical (ignoring the metric name). If no match exists, the series is dropped.

```promql
# One-to-one: instance labels must match exactly
http_requests_total / http_requests_total_error

# Series from left side with no matching partner on right are dropped
rate(http_requests_total[5m]) + rate(http_requests_total_error[5m])
```

For many-to-one or many-to-many matching, use the `on` and `group_left` / `group_right` modifiers:

```promql
# Many-to-one: join on job; use the single series from the right
sum by (job, endpoint) (rate(http_requests_total[5m]))
  / on (job)
  group_left
  sum by (job) (rate(http_requests_total[5m]))

# Many-to-many: match on region, allow multiple left and right series
rate(http_requests_total[5m])
  / on (region)
  group_left (instance)
  rate(http_requests_total_capacity[5m])
```

The `group_left` keyword tells Prometheus to keep all series from the left side and match them with potentially multiple right-side series. `group_left (label1, label2)` preserves those labels from the left side in the output.

### 2.7 Boolean Filters and Aggregations

Boolean operators produce 1 for true and 0 for false, enabling conditional aggregations:

```promql
# Sum only instances where memory is critically low (< 5% free)
sum(http_requests_total * (node_memory_MemFree_bytes / node_memory_MemTotal_bytes < 0.05))

# Count unhealthy instances (up == 0)
count(up{job="api-server"} == 0)

# Filter instances by multiple conditions
rate(http_requests_total[5m]) * ((node_memory_MemFree_bytes / node_memory_MemTotal_bytes) < 0.1)
```

Boolean operations short-circuit: if the left side is true (non-zero), the result is the value of the right side; if the left side is false (zero), the result is zero. This allows intuitive conditional expressions.

---

## 3. High-Performance Optimization & Failure Modes

### 3.1 Recording Rules: Pre-Computed Results at Scrape Time

Recording rules evaluate PromQL expressions at fixed intervals (typically aligned with your scrape interval) and store the results as new metrics. This decouples expensive query logic from dashboard and alert evaluation, dramatically reducing Prometheus's CPU and query latency.

A recording rule is defined in Prometheus's rules configuration:

```yaml
# prometheus-rules.yml
groups:
  - name: application_metrics
    interval: 15s  # Evaluate every 15 seconds (aligned with scrape)
    rules:
      # Simple rate recording
      - record: http_requests:rate1m
        expr: rate(http_requests_total[1m])

      # Quantile recording for latency
      - record: http_request_duration:p95
        expr: |
          histogram_quantile(0.95,
            sum by (le, job, endpoint) (
              rate(http_request_duration_seconds_bucket[5m])
            )
          )

      # Per-job aggregation
      - record: http_requests:by_job:rate1m
        expr: sum by (job) (rate(http_requests_total[1m]))

      # Error rate
      - record: http_error_rate:rate1m
        expr: |
          sum by (job, endpoint) (
            rate(http_requests_total{status=~"5.."}[1m])
          ) / sum by (job, endpoint) (
            rate(http_requests_total[1m])
          )

      # Complex multi-metric correlation
      - record: cpu_utilization:ratio
        expr: |
          sum by (instance) (rate(node_cpu_seconds_total{mode!="idle"}[1m]))
          /
          sum by (instance) (rate(node_cpu_seconds_total[1m]))
```

Prometheus applies recording rules in order within a group. Later rules can reference earlier rules:

```yaml
groups:
  - name: layered_rules
    interval: 15s
    rules:
      - record: requests:rate
        expr: rate(http_requests_total[1m])

      - record: requests:error_rate
        expr: |
          rate(http_requests_total{status=~"5.."}[1m])
          /
          requests:rate

      - record: requests:error_rate:alerts
        expr: requests:error_rate > 0.05
```

The output of a recording rule is a new metric with the name specified in `record`. If the original query has labels, those labels are preserved in the recorded metric. If the query includes a `by` or `without` clause, only those labels appear in the output.

```promql
# Recording rule produces:
# http_requests:rate1m{job="api-server", instance="10.0.1.5:9090"} = 150.5

# Dashboard queries then reference the pre-computed rule:
http_requests:rate1m{job="api-server"}
```

**Performance impact:** Recording rules trade storage for query performance. Each rule adds one new time series per distinct label combination. A rule like `sum by (job, endpoint) (...)` creates a new series for every unique (job, endpoint) pair. On a large deployment with 50 jobs and 200 endpoints per job, that is 10,000 new series per rule. Monitor your cardinality and rule overhead using `topk(10, count by (__name__) (ALERTS))`.

### 3.2 Alertmanager Architecture and Routing

Alertmanager is a separate component that receives alert notifications from Prometheus, deduplicates them, routes them to appropriate receivers, and manages silences and inhibitions. Understanding Alertmanager's routing tree is essential for production deployments because a misconfigured route can either silence critical alerts or spam on-call engineers with duplicate notifications.

Alertmanager's core data structure is a **routing tree**—a hierarchical set of matchers that determine where each alert is delivered. The tree is evaluated top-to-bottom, and the first matching route handles the alert.

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/...'

route:
  # Top-level catch-all route
  receiver: default-receiver
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s        # Wait 30 seconds before sending first notification
  group_interval: 5m     # Re-evaluate grouping every 5 minutes
  repeat_interval: 4h    # Re-send notification after 4 hours of silence

  # Route for critical infrastructure alerts
  routes:
    - matchers:
        - alertname = 'KubernetesPodCrashLooping'
        - severity = 'critical'
      receiver: critical-responder-pagerduty
      group_wait: 0s
      repeat_interval: 15m

    # Route for application errors
    - matchers:
        - alertname = 'HighErrorRate'
        - severity =~ 'warning|critical'
      receiver: team-app
      continue: true  # Continue evaluating nested routes

      # Nested route for specific teams
      routes:
        - matchers:
            - team = 'payments'
          receiver: payments-slack
          group_by: ['alertname', 'cluster']

        - matchers:
            - team = 'auth'
          receiver: auth-slack
          group_by: ['alertname', 'cluster']

    # Route for low-priority alerts
    - matchers:
        - severity = 'info'
      receiver: dev-channel
      group_wait: 5m
      repeat_interval: 24h

receivers:
  - name: default-receiver
    slack_configs:
      - channel: '#monitoring'

  - name: critical-responder-pagerduty
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .GroupLabels.alertname }}'

  - name: team-app
    slack_configs:
      - channel: '#app-alerts'

  - name: payments-slack
    slack_configs:
      - channel: '#payments-team'

  - name: auth-slack
    slack_configs:
      - channel: '#auth-team'

  - name: dev-channel
    slack_configs:
      - channel: '#dev-log'

inhibit_rules:
  # Suppress warning-level alerts if the same alertname is firing at critical
  - source_matchers:
      - severity = 'critical'
    target_matchers:
      - severity = 'warning'
    equal: ['alertname', 'cluster']

  # Suppress all alerts if the cluster is down
  - source_matchers:
      - alertname = 'ClusterDown'
    target_matchers:
      - severity =~ 'warning|critical'
    equal: ['cluster']
```

#### Routing Logic: Matchers and Hierarchies

Each route can have matchers that filter alerts based on label values. Matchers use the same operators as PromQL label matching (`=`, `!=`, `=~`, `!~`). An alert is routed through the first route whose matchers all match the alert's labels.

```yaml
routes:
  # Alert must have alertname = PodCrashLooping AND severity = critical
  - matchers:
      - alertname = 'PodCrashLooping'
      - severity = 'critical'
    receiver: critical-pager

  # Alert must have status matching staging OR canary
  - matchers:
      - environment =~ 'staging|canary'
    receiver: staging-team
```

If a route has nested routes (`routes` within `routes`), Alertmanager first checks the parent route's matchers. If they match, it then evaluates the child routes. This creates a decision tree.

```yaml
route:
  receiver: default

  routes:
    # Parent route: any critical alert
    - matchers:
        - severity = 'critical'
      receiver: critical-team

      routes:
        # Child route: critical database alerts
        - matchers:
            - alertname =~ 'Database.*'
          receiver: dba-team
```

An alert matching the parent route can still be re-routed through a child route if the child's matchers also match. By default, once a route matches, evaluation stops (`continue: false`). Set `continue: true` to allow the alert to also match sibling routes.

#### Grouping and Throttling: Reducing Alert Fatigue

Alertmanager groups related alerts and batches notifications to prevent overwhelming on-call engineers. Grouping rules are specified with `group_by`:

```yaml
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
```

- **group_by:** Alerts are grouped if all specified labels have identical values. If an alert lacks a label, it is treated as having the value `""` (empty string). Alerts with no matching group create a new group.
- **group_wait:** After the first alert in a group arrives, wait this long before sending the notification. This allows time for related alerts to arrive and be batched together.
- **group_interval:** If new alerts arrive in an existing group, re-evaluate and re-send after this interval.
- **repeat_interval:** If a group has not been resolved (all alerts in it have not fired for resolve_timeout), re-send the notification after this interval.

For critical infrastructure alerts, use aggressive timing:

```yaml
- matchers:
    - severity = 'critical'
  receiver: critic
