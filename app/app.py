from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "application_http_requests_total",
    "Total number of HTTP requests received",
    ["method", "endpoint"],
)


@app.get("/")
def home():
    """Return basic application information."""
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint="/",
    ).inc()

    return jsonify(
        {
            "application": "Enterprise DevSecOps Platform",
            "message": "Application is running successfully",
            "status": "running",
            "version": "1.0.0",
        }
    ), 200


@app.get("/health")
def health():
    """Confirm that the application process is running."""
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint="/health",
    ).inc()

    return jsonify(
        {
            "service": "enterprise-devsecops-platform",
            "status": "healthy",
        }
    ), 200


@app.get("/ready")
def ready():
    """Confirm that the application is ready to receive traffic."""
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint="/ready",
    ).inc()

    return jsonify(
        {
            "service": "enterprise-devsecops-platform",
            "status": "ready",
        }
    ), 200


@app.get("/metrics")
def metrics():
    """Expose application metrics in Prometheus format."""
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint="/metrics",
    ).inc()

    return Response(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST,
    )


@app.errorhandler(404)
def not_found(error):
    """Return a structured JSON response for invalid endpoints."""
    return jsonify(
        {
            "error": "Not Found",
            "message": "The requested endpoint does not exist",
        }
    ), 404


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )