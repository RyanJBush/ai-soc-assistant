from fastapi.testclient import TestClient


def auth_headers(client: TestClient, username: str = "analyst", password: str = "analyst123!") -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
