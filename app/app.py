import time
import random
import structlog
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

# Tracing — sends to OTel Collector via HTTP
resource = Resource.create({"service.name": "observability-demo"})
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "Request latency",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)
ERROR_COUNT = Counter("http_errors_total", "Total errors", ["endpoint"])

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def record_metrics(response):
    latency = time.time() - request.start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status_code=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, '032x')
    log.info("request",
        method=request.method,
        path=request.path,
        status=response.status_code,
        latency_ms=round(latency * 1000, 2),
        trace_id=trace_id
    )
    return response

@app.route("/")
def index():
    return jsonify({"service": "observability-demo", "status": "running"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/work")
def work():
    with tracer.start_as_current_span("process-work"):
        time.sleep(random.uniform(0.01, 0.15))
        return jsonify({"result": "done"})

@app.route("/error")
def error():
    ERROR_COUNT.labels(endpoint="/error").inc()
    log.error("simulated_error", reason="intentional test error")
    return jsonify({"error": "simulated failure"}), 500

@app.route("/slow")
def slow():
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
    return jsonify({"delay_seconds": round(delay, 2)})

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    log.info("starting", port=5000)
    app.run(host="0.0.0.0", port=5000)
