import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from approval_service import (
    approve_request,
    get_approval,
    list_pending_requests,
    reject_request,
    request_approval,
)


def make_approval():
    approval_id = str(uuid.uuid4())

    result = request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Test User",
            "title": "CEO",
            "company": "Test Company",
            "lead_score": 90,
        },
        created_at="2026-08-11T00:00:00+00:00",
    )

    return approval_id, result


def test_request_approval_creates_pending_request():
    approval_id, result = make_approval()

    assert result["success"] is True
    assert result["status"] == "pending"
    assert result["approval_id"] == approval_id

    stored = get_approval(approval_id)

    assert stored["success"] is True
    assert stored["status"] == "pending"
    assert stored["action"] == "create_crm_lead"


def test_pending_request_is_listed():
    approval_id, _ = make_approval()

    result = list_pending_requests()

    assert result["success"] is True
    assert result["count"] >= 1

    approval_ids = {
        request["approval_id"]
        for request in result["requests"]
    }

    assert approval_id in approval_ids


def test_approval_changes_status_to_approved():
    approval_id, _ = make_approval()

    result = approve_request(approval_id)

    assert result["success"] is True
    assert result["status"] == "approved"

    stored = get_approval(approval_id)

    assert stored["status"] == "approved"
    assert stored["resolved_at"] is not None


def test_rejection_changes_status_to_rejected():
    approval_id, _ = make_approval()

    result = reject_request(approval_id)

    assert result["success"] is True
    assert result["status"] == "rejected"

    stored = get_approval(approval_id)

    assert stored["status"] == "rejected"
    assert stored["resolved_at"] is not None


def test_cannot_approve_rejected_request():
    approval_id, _ = make_approval()

    reject_request(approval_id)

    result = approve_request(approval_id)

    assert result["success"] is False
    assert result["status"] == "already_resolved"


def test_cannot_reject_approved_request():
    approval_id, _ = make_approval()

    approve_request(approval_id)

    result = reject_request(approval_id)

    assert result["success"] is False
    assert result["status"] == "already_resolved"


def test_unknown_approval_returns_not_found():
    result = get_approval(
        "does-not-exist"
    )

    assert result["success"] is False
    assert result["status"] == "not_found"