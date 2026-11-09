from fastapi.testclient import TestClient

RATE_LIMIT = 60


def test_ac1_clients_exceeding_sixty_requests_receive_problem_json_429(client: TestClient) -> None:
    for _ in range(RATE_LIMIT):
        r = client.get("/projects")
        assert r.status_code == 200

    r = client.get("/projects")

    assert r.status_code == 429
    assert r.headers["content-type"].startswith("application/problem+json")
    assert "Retry-After" in r.headers
    assert r.headers["Retry-After"].isdigit()
    assert int(r.headers["Retry-After"]) >= 0
    assert r.json() == {
        "type": "about:blank",
        "title": "Too Many Requests",
        "status": 429,
        "detail": "Rate limit exceeded. Retry after the number of seconds in the Retry-After header.",
    }


def test_ac2_get_health_is_never_rate_limited(client: TestClient) -> None:
    for _ in range(RATE_LIMIT + 1):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
