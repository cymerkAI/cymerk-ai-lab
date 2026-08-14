import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

# ============================================================
# PATH SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT API
# ============================================================

from approval_api import app
from approval_service import request_approval


# ============================================================
# TEST CLIENT
# ============================================================

client = TestClient(app)


# ============================================================
# HEALTH
# ============================================================

def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "approval-api"


# ============================================================
# LIST PENDING APPROVALS
# ============================================================

def test_pending_approvals_endpoint():
    response = client.get("/approvals/pending")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "count" in data
    assert "requests" in data
    assert isinstance(data["requests"], list)


# ============================================================
# GET APPROVAL
# ============================================================

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


# ============================================================
# GET UNKNOWN APPROVAL
# ============================================================

def test_get_unknown_approval_returns_404():
    response = client.get(
        "/approvals/does-not-exist"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"]["success"] is False
    assert data["detail"]["status"] == "not_found"


# ============================================================
# APPROVE APPROVAL
# ============================================================

def test_approve_approval_endpoint():
    approval_id = str(uuid.uuid4())

    request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Approve API User",
            "title": "CEO",
            "company": "Approve API Company",
            "lead_score": 95,
        },
        created_at="2026-08-14T00:00:00+00:00",
    )

    response = client.post(
        f"/approvals/{approval_id}/approve"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["approval_id"] == approval_id
    assert data["status"] == "approved"
    assert data["action"] == "create_crm_lead"
    assert data["lead"]["company"] == "Approve API Company"


# ============================================================
# REJECT APPROVAL
# ============================================================

def test_reject_approval_endpoint():
    approval_id = str(uuid.uuid4())

    request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Reject API User",
            "title": "CEO",
            "company": "Reject API Company",
            "lead_score": 80,
        },
        created_at="2026-08-14T00:00:00+00:00",
    )

    response = client.post(
        f"/approvals/{approval_id}/reject"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["approval_id"] == approval_id
    assert data["status"] == "rejected"
    assert data["action"] == "create_crm_lead"
    assert data["lead"]["company"] == "Reject API Company"


# ============================================================
# APPROVE UNKNOWN APPROVAL
# ============================================================

def test_approve_unknown_approval_returns_404():
    response = client.post(
        "/approvals/does-not-exist/approve"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"]["success"] is False
    assert data["detail"]["status"] == "not_found"


# ============================================================
# REJECT UNKNOWN APPROVAL
# ============================================================

def test_reject_unknown_approval_returns_404():
    response = client.post(
        "/approvals/does-not-exist/reject"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"]["success"] is False
    assert data["detail"]["status"] == "not_found"


# ============================================================
# TERMINAL STATE: REJECTED -> CANNOT APPROVE
# ============================================================

def test_cannot_approve_already_rejected_approval():
    approval_id = str(uuid.uuid4())

    request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Rejected User",
            "title": "CEO",
            "company": "Rejected Company",
            "lead_score": 70,
        },
        created_at="2026-08-14T00:00:00+00:00",
    )

    reject_response = client.post(
        f"/approvals/{approval_id}/reject"
    )

    assert reject_response.status_code == 200

    reject_data = reject_response.json()

    assert reject_data["success"] is True
    assert reject_data["status"] == "rejected"

    approve_response = client.post(
        f"/approvals/{approval_id}/approve"
    )

    assert approve_response.status_code == 409

    data = approve_response.json()

    assert data["detail"]["success"] is False
    assert data["detail"]["status"] == "already_resolved"


# ============================================================
# TERMINAL STATE: APPROVED -> CANNOT REJECT
# ============================================================

def test_cannot_reject_already_approved_approval():
    approval_id = str(uuid.uuid4())

    request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Approved User",
            "title": "CEO",
            "company": "Approved Company",
            "lead_score": 75,
        },
        created_at="2026-08-14T00:00:00+00:00",
    )

    approve_response = client.post(
        f"/approvals/{approval_id}/approve"
    )

    assert approve_response.status_code == 200

    approve_data = approve_response.json()

    assert approve_data["success"] is True
    assert approve_data["status"] == "approved"

    reject_response = client.post(
        f"/approvals/{approval_id}/reject"
    )

    assert reject_response.status_code == 409

    data = reject_response.json()

    assert data["detail"]["success"] is False
    assert data["detail"]["status"] == "already_resolved"