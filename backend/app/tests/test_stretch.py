import os
from unittest.mock import patch, MagicMock

def test_near_duplicate_flagged(client):
    first = client.post("/requests", json={"raw_text": "Sales wants a weekly dashboard exporting pipeline data to CSV."})
    second = client.post("/requests", json={"raw_text": "Sales wants a weekly dashboard exporting pipeline data to CSV please."})
    assert second.json()["duplicate_of"] == first.json()["id"]

def test_unrelated_requests_not_flagged(client):
    client.post("/requests", json={"raw_text": "Sales wants a weekly dashboard exporting pipeline data to CSV."})
    second = client.post("/requests", json={"raw_text": "HR needs a tool to track onboarding tasks."})
    assert second.json()["duplicate_of"] is None

def test_reviewer_endpoints_require_token_when_set(client):
    with patch.dict(os.environ, {"REVIEWER_TOKEN": "secret"}):
        resp = client.get("/requests")
        assert resp.status_code == 401
        resp = client.get("/requests", headers={"X-Reviewer-Token": "secret"})
        assert resp.status_code == 200

def test_webhook_fires_on_accept(client):
    created = client.post("/requests", json={"raw_text": "Finance needs an automated expense report."})
    req_id = created.json()["id"]
    with patch.dict(os.environ, {"WEBHOOK_URL": "https://example.com/hook"}):
        with patch("httpx.post") as mock_post:
            client.patch(f"/requests/{req_id}", json={"status": "accepted"})
            mock_post.assert_called_once()

def test_csv_export_returns_200(client):
    resp = client.get("/requests/export/csv")
    assert resp.status_code == 200