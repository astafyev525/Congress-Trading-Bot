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

    def test_duplicate_registration_fails(self, client: TestClient, test_user):
        user_data = {
            "email": test_user.email,
            "password": "differentpassword",
            "full_name": "Different Name"
        }

        response = client.post("/auth/register", json = user_data)

        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

    def test_user_login_success(self, client: TestClient, test_user):
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }

        response = client.post("/auth/login", json = login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50

    def test_user_login_wrong_password(self, client: TestClient, test_user):
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }    

        response = client.post("/auth/login", json = login_data)

        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()

    def test_user_login_nonexistent(self, client: TestClient):
        login_data = {
            "email": "doesnotexist@test.com",
            "password": "password"
        }

        response = client.post("/auth/login", json = login_data)
        
        assert response.status_code == 401

    def test_protected_route_requires_auth(self, client: TestClient):

        response = client.get("/auth/me")
        assert response.status_code == 403

    def test_protected_route_with_auth(self, client: TestClient, auth_headers):
        response = client.get("/auth/me", headers = auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data
        assert data["is_active"] == True

class TestTradeEndpoints:
    def test_get_trades_empty(self, client: TestClient):
        response = client.get("/api/trades")

        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "pagination" in data
        assert len(data["trades"]) ==0
        assert data["pagination"]["total"] == 0

    def test_get_trades_with_data(self, client: TestClient, sample_trades):
        response = client.get("/api/trades")

        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) ==2
        assert data["pagination"]["total"] == 2

        trade = data["trades"][0]
        assert "politician_name" in trade
        assert "ticker" in trade
        assert "trade_type" in trade
        assert "estimated_amount" in trade
        assert "transaction_date" in trade
    def test_get_trades_with_filters(self, client: TestClient, sample_trades):
        response = client.get("/api/trades?politician=Nancy")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) ==2

        response = client.get("/api/trades?ticker=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len*(data["trades"]) ==1
        assert data["trades"][0]["ticker"] == "AAPL"

        response = client.get("/api/trades?trade_type=Buy")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["trade_type"] == "Buy"

    def test_get_trades_pagination(self, client: TestClient, sample_trades):
        response = client.get("/api/trades?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) ==1 
        assert data["pagination"]["has_more"] == True

        response = client.get("/api/trades?limit=1&offset=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) ==1
        assert data["pagination"]["has_more"] == False

class TestPoliticianEndpoints:
    def test_get_politicians(self, client: TestClient, sample_politician):
        response = client.get("/api/politicians")
        assert response.status_code == 200
        data = response.json()
        assert "politicians" in data
        assert len(data["politicians"]) == 1

        politician = data["politicians"][0]
        assert politician["name"] == "Nancy Pelosi"
        assert politician["chamber"] == "House"
        assert politician["party"] == "Democratic"
    
    def test_get_politician_trades(self, client: TestClient, sample_politician, sample_trades):
        politician_id = sample_politician.id

        response = client.get(f"/api/politicians/{politician_id}/trades")

        assert response.status_code == 200
        data = response.json()
        assert "politician" in data
        assert "trades" in data
        assert len(data["trades"]) == 2
        assert data["politician"]["name"] == "Nancy Pelosi"

    def test_get_nonexistent_politician_trades(self, client: TestClient):
        response = client.get("/api/politicians/99999/trades")

        assert response.status_code == 404

class TestAnalyticsEndpoints:
    def test_analytics_summary(self, client: TestClient, sample_trades):
        response = client.get("/api/analytics/summary")

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "top_traders" in data

        summary = data["summary"]
        assert summary["total_trades"] == 2
        assert summary["total_volume"] > 0
        assert summary["average_trade_size"] > 0

class TestAdminEndpoints:
    def test_admin_sync_requires_auth(self, client: TestClient):
        response = client.post("/admin/sync-trades")

        assert response.status_code == 401
    
    def test_admin_sync_with_auth(self, client: TestClient, auth_headers):
        response = client.post("/admin/sync-trades", headers = auth_headers)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "direct_sync" in data

    def test_system_status_with_auth(self, client: TestClient, auth_headers):
        response = client.get("/admin/system-status", headers = auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "timestamp" in data
        assert data["database"]["status"] == "connected"

class TestErrorHandling:
    def test_invalid_endpoint(self, client: TestClient):
        response = client.get("/does-not-exist")
        assert response.status_code == 404

    def test_invalid_method(self, client: TestClient):
        response = client.post("/")

        assert response.status_code == 405

    def test_invalid_json(self, client: TestClient):
        response = client.post(
            "/auth/login",
            data = "invalid json{",
            headers = {"Content-type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client: TestClient):
        response = client.post("/auth/register", json = {"email": "test@test.com"})
        assert response.status_code == 422

        response = client.post("/auth/login", json = {"password": "test123"})

