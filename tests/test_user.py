from fastapi.testclient import TestClient
from Docker.main import app

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/users/1",
        json={"name": "Mohan", "role": "Backend Developer"}
    )
    assert response.status_code == 200

def test_get_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Mohan"

def test_put_user():
    response = client.put(
        "/users/1",
        json={"name": "Mohan Reddy", "role": "Senior Developer"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "Senior Developer"

def test_patch_user():
    response = client.patch("/users/1", params={"role": "Tech Lead"})
    assert response.status_code == 200
    assert response.json()["role"] == "Tech Lead"

def test_delete_user():
    response = client.delete("/users/1")
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"

def test_get_deleted_user():
    response = client.get("/users/1")
    assert response.status_code == 404
