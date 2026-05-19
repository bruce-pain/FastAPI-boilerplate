import pytest
from fastapi import status

from app.features.auth.jwt import create_jwt_token


@pytest.fixture
def test_user_data():
    return {"email": "test@example.com", "password": "testpassword123"}


@pytest.fixture
def registered_user(client, test_user_data):
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


class TestRegister:
    def test_register_success(self, client, test_user_data):
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["data"]["email"] == test_user_data["email"]

    def test_register_duplicate_email(self, client, test_user_data):
        client.post("/api/v1/auth/register", json=test_user_data)
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["message"]

    def test_register_invalid_email(self, client):
        response = client.post(
            "/api/v1/auth/register", json={"email": "invalid-email", "password": "password123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields(self, client):
        response = client.post("/api/v1/auth/register", json={"email": "test@example.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    def test_login_success(self, client, test_user_data):
        client.post("/api/v1/auth/register", json=test_user_data)
        response = client.post(
            "/api/v1/auth/login", json={"email": test_user_data["email"], "password": test_user_data["password"]}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "User logged in successfully"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_email(self, client):
        response = client.post(
            "/api/v1/auth/login", json={"email": "nonexistent@example.com", "password": "password123"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid email" in response.json()["message"]

    def test_login_invalid_password(self, client, test_user_data):
        client.post("/api/v1/auth/register", json=test_user_data)
        response = client.post(
            "/api/v1/auth/login", json={"email": test_user_data["email"], "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid password" in response.json()["message"]


class TestTokenRefresh:
    def test_refresh_token_success(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/token/refresh", json={"refresh_token": registered_user["refresh_token"]}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_refresh_token_invalid(self, client):
        response = client.post(
            "/api/v1/auth/token/refresh", json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUser:
    def test_get_user_success(self, client, registered_user):
        access_token = registered_user["access_token"]
        response = client.get(
            "/api/v1/auth/user", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["email"] == "test@example.com"

    def test_get_user_unauthorized(self, client):
        response = client.get("/api/v1/auth/user")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_invalid_token(self, client):
        response = client.get(
            "/api/v1/auth/user", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED