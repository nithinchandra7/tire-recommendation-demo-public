from fastapi.testclient import TestClient
from tire_demo.app import create_app


def test_remote_peer_cannot_select_a_privileged_demo_identity(settings):
    with TestClient(create_app(settings), client=("203.0.113.8", 40000)) as client:
        response = client.get("/api/tire/options", headers={"X-Demo-Retailer": "north"})
        assert response.status_code == 403


def test_untrusted_host_and_cross_origin_requests_fail_before_identity(client, headers):
    for extra in [
        {"Host": "attacker.example"},
        {"Origin": "https://attacker.example"},
        {"Origin": "null"},
        {"Origin": "http://testserver:9999"},
        {"Origin": "http://user:password@testserver"},
        {"Sec-Fetch-Site": "cross-site"},
    ]:
        response = client.get("/api/tire/options", headers=headers | extra)
        assert response.status_code == 403


def test_same_origin_local_request_and_security_headers(client, headers):
    response = client.get("/api/tire/options", headers=headers | {"Origin": "http://testserver"})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_encoded_traversal_does_not_reveal_source_or_secrets(client):
    for path in ["/.env", "/.git/HEAD", "/%2e%2e/pyproject.toml", "/assets/%2e%2e/%2e%2e/.env"]:
        assert client.get(path).status_code == 404
