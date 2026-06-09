# Full Observability Stack

A complete three-pillar observability stack shipping metrics, logs, and distributed traces to Grafana Cloud using OpenTelemetry.
Every request is tracked end-to-end — from HTTP hit to trace span, structured log, and Prometheus metric — all correlated by trace_id.

---

## Architecture

Flask App → OTel Collector → Grafana Cloud
├── Prometheus (metrics)
├── Loki (logs)
└── Tempo (traces)

Logs include a `trace_id` field — click a log line in Loki and jump directly to the matching trace in Tempo. Full correlation across all three pillars.

---

## Key highlights

- P95 latency tracked per endpoint using Prometheus histograms
- Every log line carries a `trace_id` — logs and traces are fully correlated
- OTel Collector decouples the app from the backend — swap Grafana Cloud for any OTLP-compatible backend without touching app code
- Simulated failure endpoints (`/error`, `/slow`) for realistic alert testing

---

## Stack

| Tool | Purpose |
|---|---|
| Flask | Instrumented Python microservice |
| Prometheus client | Exposes `/metrics` endpoint |
| OpenTelemetry SDK | Auto-instruments traces and context propagation |
| Structlog | Structured JSON logging with trace_id injection |
| OTel Collector | Receives all telemetry, routes to Grafana Cloud |
| Grafana Cloud | Unified dashboard — metrics + logs + traces |

---


## What is instrumented

- **Metrics** — request count, error count, P95 latency per endpoint
- **Traces** — every request generates a trace with spans
- **Logs** — structured JSON with `trace_id` for cross-pillar correlation

---

## Grafana Dashboard

Three panels tracking the golden signals:

| Panel | Query |
|---|---|
| Request Rate | `rate(http_requests_total[5m])` |
| Error Rate | `http_errors_total` |
| P95 Latency | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` |

![Observability Dashboard](dashboard.png)

---

## Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Index |
| `/health` | Health check |
| `/work` | Simulates processing with random latency |
| `/error` | Simulates 500 errors |
| `/slow` | Simulates slow responses (0.5–2s) |
| `/metrics` | Prometheus scrape endpoint |

---

## Run locally

```bash
# Add credentials to .env (see .env.example)
docker compose up -d

# Generate traffic
curl http://localhost:5000/work
curl http://localhost:5000/error

# Stop
docker compose down
```

---

## What I learned

- How the three pillars of observability (metrics, logs, traces) work 
  together — and why each one alone is not enough
- How OpenTelemetry decouples instrumentation from the backend — 
  one SDK, any compatible backend
- How to correlate logs and traces using trace_id — turning isolated 
  log lines into a full request journey
- How to write PromQL queries for real signals: request rate, 
  error rate, and latency percentiles
- Why P95 latency matters more than averages for catching real 
  performance issues
