# lesson 2 deliberate failure — this test is intentionally wrong, to prove
# the commit gate and CI both actually catch a red build instead of just
# looking like they would.

from fastapi.testclient import TestClient

from app.main import app


def test_deliberately_wrong() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.json() == {"status": "deliberately wrong"}
