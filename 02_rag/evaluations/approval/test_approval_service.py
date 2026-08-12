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

def test_duplicate_approval_id_is_rejected():
    approval_id, first = make_approval()

    assert first["success"] is True
    assert first["status"] == "pending"

    duplicate = request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Another User",
            "title": "CFO",
            "company": "Another Company",
            "lead_score": 95,
        },
        created_at="2026-08-11T01:00:00+00:00",
    )

    assert duplicate["success"] is False
    assert duplicate["status"] == "already_exists"

    stored = get_approval(approval_id)

    assert stored["success"] is True
    assert stored["status"] == "pending"
    assert stored["lead"]["name"] == "Test User"
    assert stored["lead"]["company"] == "Test Company"


def test_approved_request_cannot_be_approved_again():
    approval_id, _ = make_approval()

    first = approve_request(approval_id)

    assert first["success"] is True
    assert first["status"] == "approved"

    second = approve_request(approval_id)

    assert second["success"] is False
    assert second["status"] == "already_resolved"

def test_approved_request_cannot_be_approved_again():
    approval_id, _ = make_approval()

    first = approve_request(approval_id)

    assert first["success"] is True
    assert first["status"] == "approved"

    second = approve_request(approval_id)

    assert second["success"] is False
    assert second["status"] == "already_resolved"
    assert second["approval_id"] == approval_id


def test_approval_cannot_be_created_with_existing_id():
    approval_id, first = make_approval()

    assert first["success"] is True
    assert first["status"] == "pending"

    duplicate = request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Different User",
            "title": "CFO",
            "company": "Different Company",
            "lead_score": 50,
        },
        created_at="2026-08-12T00:00:00+00:00",
    )

    assert duplicate["success"] is False
    assert duplicate["status"] == "already_exists"

    stored = get_approval(approval_id)

    assert stored["lead"]["name"] == "Test User"
    assert stored["lead"]["company"] == "Test Company"

def test_approval_state_transition_is_terminal():
    approval_id, _ = make_approval()

    approved = approve_request(approval_id)

    assert approved["success"] is True
    assert approved["status"] == "approved"

    rejected = reject_request(approval_id)

    assert rejected["success"] is False
    assert rejected["status"] == "already_resolved"

    approved_again = approve_request(approval_id)

    assert approved_again["success"] is False
    assert approved_again["status"] == "already_resolved"