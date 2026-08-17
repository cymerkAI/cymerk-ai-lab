import sys
import uuid
from pathlib import Path

import pytest


# ============================================================
# PROJECT IMPORT CONFIGURATION
# ============================================================

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


# ============================================================
# TEST HELPERS
# ============================================================

def make_approval():
    """
    Create a valid pending approval request for testing.

    Returns:
        tuple[str, dict]: approval ID and service response.
    """

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


# ============================================================
# REQUEST APPROVAL
# ============================================================

def test_request_approval_creates_pending_request():
    """
    A new approval request must be stored as pending.
    """

    approval_id, result = make_approval()

    assert result["success"] is True
    assert result["status"] == "pending"
    assert result["approval_id"] == approval_id

    stored = get_approval(approval_id)

    assert stored["success"] is True
    assert stored["status"] == "pending"
    assert stored["action"] == "create_crm_lead"


# ============================================================
# LIST PENDING APPROVALS
# ============================================================

def test_pending_request_is_listed():
    """
    A pending approval must appear in the pending-approval list.
    """

    approval_id, _ = make_approval()

    result = list_pending_requests()

    assert result["success"] is True
    assert result["count"] >= 1

    approval_ids = {
        request["approval_id"]
        for request in result["requests"]
    }

    assert approval_id in approval_ids


# ============================================================
# APPROVE REQUEST
# ============================================================

def test_approval_changes_status_to_approved():
    """
    A pending approval can be transitioned to approved.
    """

    approval_id, _ = make_approval()

    result = approve_request(approval_id)

    assert result["success"] is True
    assert result["status"] == "approved"
    assert result["approval_id"] == approval_id

    stored = get_approval(approval_id)

    assert stored["status"] == "approved"
    assert stored["resolved_at"] is not None


# ============================================================
# REJECT REQUEST
# ============================================================

def test_rejection_changes_status_to_rejected():
    """
    A pending approval can be transitioned to rejected.
    """

    approval_id, _ = make_approval()

    result = reject_request(approval_id)

    assert result["success"] is True
    assert result["status"] == "rejected"
    assert result["approval_id"] == approval_id

    stored = get_approval(approval_id)

    assert stored["status"] == "rejected"
    assert stored["resolved_at"] is not None


# ============================================================
# TERMINAL STATE PROTECTION
# ============================================================

def test_cannot_approve_rejected_request():
    """
    A rejected approval cannot subsequently be approved.
    """

    approval_id, _ = make_approval()

    reject_request(approval_id)

    result = approve_request(approval_id)

    assert result["success"] is False
    assert result["status"] == "already_resolved"
    assert result["approval_id"] == approval_id


def test_cannot_reject_approved_request():
    """
    An approved request cannot subsequently be rejected.
    """

    approval_id, _ = make_approval()

    approve_request(approval_id)

    result = reject_request(approval_id)

    assert result["success"] is False
    assert result["status"] == "already_resolved"
    assert result["approval_id"] == approval_id


def test_approved_request_cannot_be_approved_again():
    """
    An approved request cannot be approved a second time.
    """

    approval_id, _ = make_approval()

    first = approve_request(approval_id)

    assert first["success"] is True
    assert first["status"] == "approved"

    second = approve_request(approval_id)

    assert second["success"] is False
    assert second["status"] == "already_resolved"
    assert second["approval_id"] == approval_id


def test_approval_state_transition_is_terminal():
    """
    Once an approval reaches a resolved state, it cannot
    transition to another resolved state.
    """

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


# ============================================================
# UNKNOWN APPROVAL
# ============================================================

def test_unknown_approval_returns_not_found():
    """
    An unknown approval ID must return a not_found response.
    """

    result = get_approval(
        "does-not-exist"
    )

    assert result["success"] is False
    assert result["status"] == "not_found"


# ============================================================
# DUPLICATE APPROVAL ID PROTECTION
# ============================================================

def test_duplicate_approval_id_is_rejected():
    """
    An existing approval ID cannot be overwritten with
    a different approval request.
    """

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
    assert duplicate["approval_id"] == approval_id

    stored = get_approval(approval_id)

    assert stored["success"] is True
    assert stored["status"] == "pending"

    # Original request must remain unchanged.
    assert stored["lead"]["name"] == "Test User"
    assert stored["lead"]["company"] == "Test Company"
    assert stored["lead"]["lead_score"] == 90


def test_approval_cannot_be_created_with_existing_id():
    """
    A second request using an existing approval ID must not
    overwrite the original request.
    """

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
    assert duplicate["approval_id"] == approval_id

    stored = get_approval(approval_id)

    assert stored["success"] is True
    assert stored["status"] == "pending"

    # Original approval data must be preserved.
    assert stored["lead"]["name"] == "Test User"
    assert stored["lead"]["company"] == "Test Company"
    assert stored["lead"]["lead_score"] == 90


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    raise SystemExit(
        pytest.main(
            [__file__, "-v"]
        )
    )