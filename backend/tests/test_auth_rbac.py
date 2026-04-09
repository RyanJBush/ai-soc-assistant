from fastapi.testclient import TestClient

from backend.app.main import app
from backend.tests.conftest import auth_headers


def test_login_returns_token_and_role() -> None:
    client = TestClient(app)
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123!"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["role"] == "admin"


def test_admin_audit_endpoint_requires_admin() -> None:
    client = TestClient(app)

    viewer_resp = client.get(
        "/admin/audit/recent",
        headers=auth_headers(client, "viewer", "viewer123!"),
    )
    assert viewer_resp.status_code == 403

    admin_resp = client.get(
        "/admin/audit/recent",
        headers=auth_headers(client, "admin", "admin123!"),
    )
    assert admin_resp.status_code == 200
