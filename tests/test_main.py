from fastapi.testclient import TestClient
from Docker.main import app

client = TestClient(app)

def test_root_api():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Cognito API is running"}

def test_health_api():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"

def test_login_api():
    response = client.post("/login")
    assert response.status_code == 200
    assert "token" in response.json()
