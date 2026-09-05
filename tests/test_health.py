from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "deployment-risk-analyzer"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"