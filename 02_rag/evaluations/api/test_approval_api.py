import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from approval_api import app
from approval_service import request_approval


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "approval-api"


def test_pending_approvals_endpoint():
    response = client.get("/approvals/pending")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "count" in data
    assert "requests" in data
    assert isinstance(data["requests"], list)


def test_get_approval_endpoint():
    approval_id = str(uuid.uuid4())

    request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "API Test User",
            "title": "CEO",
            "company": "API Test Company",
            "lead_score": 90,
        },
        created_at="2026-08-14T00:00:00+00:00",
    )

    response = client.get(
        f"/approvals/{approval_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["approval_id"] == approval_id
    assert data["status"] == "pending"
    assert data["action"] == "create_crm_lead"
    assert data["lead"]["name"] == "API Test User"


def test_get_unknown_approval_returns_404():
    response = client.get(
        "/approvals/does-not-exist"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"]["success"] is False
    assert data["detail"]["status"] == "not_found"