# Checks that the app's "are you alive?" endpoint actually answers "yes" —
# this is the one test the commit gate (test-gate.sh) needs to have
# something real to run, so a broken app can never get committed silently.

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
