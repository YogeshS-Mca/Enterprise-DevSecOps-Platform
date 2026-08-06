from app.app import app


def test_home_endpoint():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200

    data = response.get_json()

    assert data["application"] == "Enterprise DevSecOps Platform"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


def test_health_endpoint():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["service"] == "enterprise-devsecops-platform"
    assert data["status"] == "healthy"


def test_ready_endpoint():
    client = app.test_client()

    response = client.get("/ready")

    assert response.status_code == 200

    data = response.get_json()

    assert data["service"] == "enterprise-devsecops-platform"
    assert data["status"] == "ready"


def test_metrics_endpoint():
    client = app.test_client()

    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"application_http_requests_total" in response.data


def test_unknown_endpoint_returns_404():
    client = app.test_client()

    response = client.get("/does-not-exist")

    assert response.status_code == 404

    data = response.get_json()

    assert data["status"] == "error"