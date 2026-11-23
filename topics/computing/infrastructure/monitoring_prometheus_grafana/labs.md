# Operational Verification Labs: Prometheus and Grafana

## Objective and Environment Setup

These labs build a small but complete monitoring stack on one machine and then break it on purpose. By the end you will have verified, with your own queries, the mechanics from Lessons 2–4: how scraping and staleness work, why `rate()` needs enough samples, what recording rules save, how Grafana provisioning and variables behave, and what a dead target looks like from every side.

**You need:** Docker with the Compose plugin (`docker compose version`), `curl`, and `jq`. Everything else runs in containers. Ports 9090 (Prometheus), 9100 (node_exporter) and 3000 (Grafana) must be free.

Create a working directory with this layout:

```text
monitoring-lab/
├── docker-compose.yml
├── prometheus/
│   ├── prometheus.yml
│   └── rules.yml
└── grafana/
    ├── provisioning/
    │   ├── datasources/prometheus.yaml
    │   └── dashboards/default.yaml
    └── dashboards/            # dashboard JSON files go here
```

`docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.53.0
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=2d
      - --web.enable-lifecycle          # allows POST /-/reload
    volumes:
      - ./prometheus:/etc/prometheus:ro
    ports: ["9090:9090"]

  node-exporter:
    image: prom/node-exporter:v1.8.1
    ports: ["9100:9100"]

  grafana:
    image: grafana/grafana:11.1.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: labpass
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports: ["3000:3000"]
```

`prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/rules.yml

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: node
    static_configs:
      - targets: ["node-exporter:9100"]
```

Start with an empty rule file (`groups: []` in `prometheus/rules.yml`), then validate the configuration *before* starting anything:

```bash
docker run --rm -v "$PWD/prometheus:/etc/prometheus:ro" --entrypoint promtool \
  prom/prometheus:v2.53.0 check config /etc/prometheus/prometheus.yml
docker compose up -d
```

Expected: `SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax`, then three running containers (`docker compose ps`).

---

## Exercise 1: Scraping, Targets and Staleness

### 1.1 Confirm both targets are healthy

```bash
curl -s localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job)\t\(.health)\t\(.lastScrapeDuration)s"'
```

Both jobs should report `up` within 15 seconds. Now ask the same question in PromQL:

```bash
curl -s 'localhost:9090/api/v1/query' --data-urlencode 'query=up' | jq -r '.data.result[] | "\(.metric.job) = \(.value[1])"'
```

`up` is not exported by any target: Prometheus writes it itself after each scrape (1 if the scrape succeeded, 0 if not). That makes it the only metric you can trust to exist when a target is dead.

### 1.2 Look at what one scrape contains

```bash
curl -s localhost:9100/metrics | grep -c '^node_'
curl -s 'localhost:9090/api/v1/query' --data-urlencode 'query=scrape_samples_scraped{job="node"}' | jq -r '.data.result[0].value[1]'
```

The two numbers are close but not equal: the second also counts non-`node_` series such as `go_*` and `process_*`. `scrape_samples_scraped` is the first metric to watch when a target's cardinality grows.

### 1.3 Measure the scrape interval from the data

```bash
curl -s 'localhost:9090/api/v1/query' \
  --data-urlencode 'query=count_over_time(up{job="node"}[1m])' | jq -r '.data.result[0].value[1]'
```

With a 15-second interval the answer is 4 (occasionally 5, depending on where the window edges fall). Keep this number in mind for Exercise 2.

### 1.4 Watch a series go stale

```bash
docker compose stop node-exporter
sleep 30
curl -s 'localhost:9090/api/v1/query' --data-urlencode 'query=up{job="node"}' | jq -r '.data.result[0].value[1]'
curl -s 'localhost:9090/api/v1/query' --data-urlencode 'query=node_load1' | jq '.data.result | length'
```

`up` is now `0`, and `node_load1` returns **no series at all**. When a scrape fails, Prometheus writes a *staleness marker* for every series the target used to expose, so queries stop returning the old value instead of repeating it for the 5-minute lookback window. Start the exporter again (`docker compose start node-exporter`) and confirm both come back.

**Checkpoint:** explain why an alert on `node_load1 > 4` can never fire while the node is down, and which expression would.

---

## Exercise 2: PromQL Windows and Recording Rules

### 2.1 Find the shortest window `rate()` can use

```bash
for w in 15s 30s 1m; do
  n=$(curl -s 'localhost:9090/api/v1/query' \
      --data-urlencode "query=rate(node_cpu_seconds_total{mode=\"idle\"}[$w])" | jq '.data.result | length')
  echo "window $w -> $n series"
done
```

With a 15-second scrape interval, `[15s]` usually returns no series or only some of them, because many windows contain a single sample and `rate()` needs two. `[30s]` is unreliable for the same reason; `[1m]` (four samples) always works. This is exactly the rule behind Grafana's `$__rate_interval` (at least four scrape intervals).

### 2.2 Compare `rate()` and `irate()`

Generate a short CPU burst, then compare both functions over the same window:

```bash
docker run --rm --name burn alpine sh -c 'timeout 40 sh -c "while :; do :; done"' &
sleep 45
curl -s 'localhost:9090/api/v1/query' --data-urlencode \
  'query=max(1 - rate(node_cpu_seconds_total{mode="idle"}[5m]))' | jq -r '.data.result[0].value[1]'
curl -s 'localhost:9090/api/v1/query' --data-urlencode \
  'query=max(1 - irate(node_cpu_seconds_total{mode="idle"}[5m]))' | jq -r '.data.result[0].value[1]'
```

Run the pair again a minute later. `rate()` averages over the whole 5 minutes, so the burst raises it a little and it falls slowly. `irate()` uses only the last two samples, so it shows the burst at full height while it lasts and drops to idle right after. Use `irate()` for "what is happening this second" graphs, `rate()` for alerts and trends.

### 2.3 Measure what a recording rule saves

Take a query that aggregates many series:

```bash
q='sum by (mode) (rate(node_cpu_seconds_total[1m]))'
curl -s 'localhost:9090/api/v1/query' --data-urlencode "query=$q" --data-urlencode 'stats=all' \
  | jq '.data.stats.samples.totalQueryableSamples'
```

The `stats=all` parameter makes Prometheus report how many samples the query read. Now record it. Replace `prometheus/rules.yml` with:

```yaml
groups:
  - name: node-cpu
    interval: 15s
    rules:
      - record: mode:node_cpu_seconds:rate1m
        expr: sum by (mode) (rate(node_cpu_seconds_total[1m]))
```

Validate, reload and query the recorded series:

```bash
docker run --rm -v "$PWD/prometheus:/etc/prometheus:ro" --entrypoint promtool \
  prom/prometheus:v2.53.0 check rules /etc/prometheus/rules.yml
curl -s -X POST localhost:9090/-/reload
sleep 30
curl -s 'localhost:9090/api/v1/query' --data-urlencode 'query=mode:node_cpu_seconds:rate1m' \
  --data-urlencode 'stats=all' | jq '.data.stats.samples.totalQueryableSamples'
```

The second number is a small fraction of the first: one series per CPU mode instead of one per CPU *and* mode, already rated. On a machine with 8 CPUs that is roughly an 8× reduction for an instant query, and the saving multiplies by the number of steps in a range query.

**Checkpoint:** the recorded series uses a fixed `[1m]` window. What does a Grafana panel lose by querying it instead of the raw expression with `$__rate_interval`?

---

## Exercise 3: Grafana as Code

### 3.1 Provision the data source

`grafana/provisioning/datasources/prometheus.yaml`:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    uid: prom-lab
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
      httpMethod: POST
```

`grafana/provisioning/dashboards/default.yaml`:

```yaml
apiVersion: 1
providers:
  - name: lab
    folder: Lab
    type: file
    allowUiUpdates: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
```

Restart Grafana and check through its API that the data source exists and can reach Prometheus:

```bash
docker compose restart grafana
sleep 10
curl -s -u admin:labpass localhost:3000/api/health | jq -r .database
curl -s -u admin:labpass localhost:3000/api/datasources/uid/prom-lab | jq -r '.name, .url'
curl -s -u admin:labpass localhost:3000/api/datasources/uid/prom-lab/health | jq -r .status
```

Expected: `ok`, then `Prometheus` and `http://prometheus:9090`, then `OK`. Note the URL: `prometheus` is the Compose service name, resolved inside the Docker network. The browser never connects to it; Grafana's server does (access mode *proxy*).

### 3.2 Build a dashboard with a variable

Create `grafana/dashboards/node.json` with a variable and one panel:

```json
{
  "uid": "lab-node",
  "title": "Lab Node",
  "time": { "from": "now-30m", "to": "now" },
  "refresh": "1m",
  "templating": {
    "list": [
      {
        "name": "instance",
        "type": "query",
        "datasource": { "type": "prometheus", "uid": "prom-lab" },
        "query": "label_values(up{job=\"node\"}, instance)",
        "multi": true,
        "includeAll": true,
        "allValue": ".*",
        "refresh": 1
      }
    ]
  },
  "panels": [
    {
      "type": "timeseries",
      "title": "CPU busy",
      "gridPos": { "x": 0, "y": 0, "w": 24, "h": 9 },
      "datasource": { "type": "prometheus", "uid": "prom-lab" },
      "targets": [
        {
          "refId": "A",
          "expr": "1 - avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\", instance=~\"$instance\"}[$__rate_interval]))",
          "legendFormat": "{{instance}}"
        }
      ],
      "fieldConfig": { "defaults": { "unit": "percentunit", "min": 0, "max": 1 } }
    }
  ]
}
```

Within 30 seconds the provider loads it. Confirm and open it:

```bash
curl -s -u admin:labpass 'localhost:3000/api/search?query=Lab%20Node' | jq -r '.[].url'
```

Open `http://localhost:3000` + that URL (log in as `admin` / `labpass`).

### 3.3 Prove the provisioning file wins

In the UI, change the panel title and try to save. Grafana refuses (*Cannot save provisioned dashboard*) because `allowUiUpdates` is `false`. Change the title in `node.json` instead and wait 30 seconds: the UI follows the file. This is the behaviour you want for shared dashboards: git is the source of truth.

### 3.4 See `$__rate_interval` change with the time range

Open the panel editor and the *Query inspector* (*Inspect → Query*). Note the interval Grafana sent for the last 30 minutes. Switch the dashboard to the last 7 days and inspect again. The step grows (from seconds to many minutes), and `$__rate_interval` grows with it, so each window still covers the gap between points.

Now edit `node.json` to use `[$__interval]` instead of `[$__rate_interval]`, set the time range to the last 5 minutes and look at the panel: it shows gaps or no data, because the window is shorter than two scrapes. Put `$__rate_interval` back.

**Checkpoint:** change the data source's `timeInterval` to `"60s"` and restart Grafana. Why does the CPU graph become smoother, and why is that misleading?

---

## Exercise 4: Fault Injection and Recovery

### 4.1 An alert on the right expression

Add an alerting rule to `prometheus/rules.yml` (keep the recording rule group):

```yaml
  - name: node-availability
    rules:
      - alert: NodeExporterDown
        expr: up{job="node"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "node_exporter on {{ $labels.instance }} is down"
```

Validate and reload as in 2.3, then break the target and watch the alert move through its states:

```bash
docker compose stop node-exporter
for i in $(seq 1 8); do
  curl -s localhost:9090/api/v1/alerts | jq -r '.data.alerts[] | "\(.labels.alertname) \(.state)"'
  sleep 15
done
docker compose start node-exporter
```

Expected sequence: nothing for the first scrape, then `pending` (the condition is true but `for: 1m` has not passed), then `firing`. After the restart the alert disappears once `up` is 1 again. The `for` clause is what keeps a single failed scrape from paging anyone.

### 4.2 Prometheus itself goes away

```bash
docker compose stop prometheus
curl -s -u admin:labpass localhost:3000/api/datasources/uid/prom-lab/health | jq -r '.status, .message'
```

Grafana stays up and reports the data source as failing; panels show an error, not zeros. Nothing was lost in Grafana, because it never held the data. Start Prometheus again: the samples written before the stop are still there (the TSDB lives in the container's data directory), and there is a gap for the time it was down.

### 4.3 A query that is too expensive

Prometheus refuses queries that would load too many samples. Lower the limit to make the failure visible on a small lab: add `--query.max-samples=1000` to the Prometheus `command` list, run `docker compose up -d prometheus`, then:

```bash
curl -s 'localhost:9090/api/v1/query_range' \
  --data-urlencode 'query=rate(node_cpu_seconds_total[5m])' \
  --data-urlencode "start=$(date -d '-30 min' +%s 2>/dev/null || date -v-30M +%s)" \
  --data-urlencode "end=$(date +%s)" --data-urlencode 'step=15' | jq -r '.error'
```

Expected: `query processing would load too many samples into memory in query execution`. The same message appears in a Grafana panel. Remove the flag and recreate the container before continuing.

---

## Diagnostic Cheat Sheet and Verification Checklist

| Question | Command or query |
|---|---|
| Is every target being scraped? | `curl -s localhost:9090/api/v1/targets \| jq '.data.activeTargets[] \| {job: .labels.job, health, lastError}'` |
| Which target is down? | `up == 0` |
| How many series does a target expose? | `scrape_samples_scraped` |
| How expensive is a query? | add `--data-urlencode 'stats=all'` and read `totalQueryableSamples` |
| Is a rule file valid? | `promtool check rules rules.yml` |
| Did the reload work? | `curl -s localhost:9090/api/v1/status/config \| jq -r .data.yaml \| head` |
| Can Grafana reach Prometheus? | `curl -s -u admin:labpass localhost:3000/api/datasources/uid/prom-lab/health` |
| What did a panel actually send? | Panel → *Inspect → Query* |

Before you finish, confirm you can answer each of these from your own results:

- [ ] Why `up` still exists when every other series of a dead target is gone.
- [ ] The shortest reliable `rate()` window for a 15-second scrape interval, and why.
- [ ] How many samples the recording rule in 2.3 saved per query on your machine.
- [ ] Why the provisioned dashboard could not be saved from the UI.
- [ ] What `pending` means for an alert, and which setting controls how long it lasts.
- [ ] What Grafana shows when Prometheus is down, and why no data was lost.

Clean up with `docker compose down -v`.
