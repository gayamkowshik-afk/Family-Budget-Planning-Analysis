"""Recruiter note: an end-to-end test of the real API: register, log in, add data, read insights,
and check the child-consent rule."""
from datetime import date

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login():
    client.post("/auth/register", json={"name": "Test", "email": "t@example.com", "password": "password123"})
    r = client.post("/auth/login", data={"username": "t@example.com", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_full_flow():
    h = _login()
    today = date.today().isoformat()
    assert client.post("/transactions", json={"date": today, "description": "SALARY ACME", "amount": 60000, "is_income": True}, headers=h).json()["added"] == 1
    client.post("/transactions", json={"date": today, "description": "SWIGGY*ORD9", "amount": 500, "txn_ref": "TX1"}, headers=h)
    dup = client.post("/transactions", json={"date": today, "description": "SWIGGY*ORD9", "amount": 500}, headers=h).json()
    assert dup["skipped_duplicates"] == 1
    s = client.get("/analytics/summary", headers=h).json()
    assert s["income"] == 60000 and s["by_category"]["Dining"] == 500
    assert client.post("/transactions/verify", json={"txn_ref": "TX1", "otp": "000000"}, headers=h).status_code == 401
    assert client.post("/transactions/verify", json={"txn_ref": "TX1", "otp": "123456"}, headers=h).json()["verified"]


def test_child_needs_both_consents():
    h = _login()
    bad = client.post("/children", json={"name": "Aarav", "allowance": 500, "parent_consent": True, "child_assent": False}, headers=h)
    assert bad.status_code == 422
    ok = client.post("/children", json={"name": "Aarav", "allowance": 500, "parent_consent": True, "child_assent": True}, headers=h)
    assert ok.status_code == 201


def test_requires_login():
    assert client.get("/transactions").status_code == 401
