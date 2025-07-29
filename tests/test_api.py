import pytest
from fastapi.testclient import TestClient

class TestHealthEndpoints:
    def test_root_endpoint(self, client: TestClient):
        response = client.get("/")

        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"
        assert "endpoints" in data

    def test_health_endpoint(self, client: TestClient):
        response = client.get("/heatlth")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data

class TestAuthenticationEndpoints:
    def test_user_registration(self, client: TestClient):
        user_data = {
            "email": "newuser@test.com",
            "password": "strongpassword123",
            "full_name": "New Test User"
        }

        response = client.post("/auth/register", json = user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] == True
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    