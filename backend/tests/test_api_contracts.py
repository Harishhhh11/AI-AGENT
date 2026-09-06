from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_public_health_contract_is_stable() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_protected_integrations_api_requires_authentication() -> None:
    response = client.get("/api/v1/integrations")

    assert response.status_code == 401


def test_openapi_exposes_phase10_integrations_route() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/integrations" in response.json()["paths"]
