from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

app = Flask(__name__)

# Prometheus Counter
REQUEST_COUNT = Counter(
    "application_http_requests_total",
    "Total number of HTTP requests received",
    ["method", "endpoint"],
)


@app.get("/")
def home():
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
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint="/metrics",
    ).inc()

    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST,
    )


@app.errorhandler(404)
def page_not_found(error):
    return (
        jsonify(
            {
                "status": "error",
                "message": "Endpoint not found",
            }
        ),
        404,
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )