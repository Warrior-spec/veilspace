from fastapi.testclient import TestClient

from veilspace.config import Settings
from veilspace.main import create_app


def test_health_does_not_expose_configuration():
    with TestClient(create_app(Settings(environment="development"))) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok", "service": "veilspace", "version": "0.1.0"
        }


def test_production_does_not_publish_api_docs():
    with TestClient(create_app(Settings(environment="production"))) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
