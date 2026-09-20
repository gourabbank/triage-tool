def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_create_request_generates_brief(client):
    resp = client.post("/requests", json={"raw_text": "Sales wants a weekly CSV export."})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "new"
    assert body["brief"]["problem_summary"]

def test_create_request_rejects_short_text(client):
    resp = client.post("/requests", json={"raw_text": "fix"})
    assert resp.status_code == 422

def test_triage_update_and_audit(client):
    created = client.post("/requests", json={"raw_text": "Testing triage update logic."})
    req_id = created.json()["id"]

    resp = client.patch(f"/requests/{req_id}", json={"status": "accepted", "owner": "bob"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    audit = client.get(f"/requests/{req_id}/audit")
    fields_changed = {e["field"] for e in audit.json()}
    assert {"status", "owner"} <= fields_changed

def test_triage_update_no_fields_rejected(client):
    created = client.post("/requests", json={"raw_text": "Testing empty patch rejection."})
    req_id = created.json()["id"]
    resp = client.patch(f"/requests/{req_id}", json={})
    assert resp.status_code == 400

def test_get_nonexistent_request_404(client):
    resp = client.get("/requests/not-a-real-id")
    assert resp.status_code == 404