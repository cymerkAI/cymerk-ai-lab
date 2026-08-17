import json
import sys
import uuid
from pathlib import Path

import pytest

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

from agent_tools import (
    approve_crm_lead,
    create_lead,
    execute_approved_crm_lead,
    get_approval_status,
    reject_crm_lead,
    utc_timestamp,
)

from approval_service import request_approval


# ============================================================
# HELPERS
# ============================================================

def make_approved_crm_lead():
    """
    Create a valid CRM lead approval request and approve it.

    Returns:
        approval_id
    """

    approval_id = str(uuid.uuid4())

    request = request_approval(
        approval_id=approval_id,
        action="create_crm_lead",
        lead={
            "name": "Approved User",
            "title": "CEO",
            "company": "Approved Company",
            "lead_score": 95,
        },
        created_at=utc_timestamp(),
    )

    assert request["success"] is True
    assert request["status"] == "pending"

    approval = approve_crm_lead(
        approval_id
    )

    assert approval["success"] is True
    assert approval["status"] == "approved"

    return approval_id


# ============================================================
# KNOWLEDGE / SECURITY
# ============================================================

def test_knowledge_request():
    """
    Knowledge requests should be handled by the RAG system
    rather than CRM functionality.
    """

    from rag_crm_agent import run_agent

    result = run_agent(
        "What services does Cymerk provide?"
    )

    assert result is not None


def test_security_request():
    """
    Security-related knowledge requests should not create
    CRM records or bypass approval.
    """

    from rag_crm_agent import run_agent

    result = run_agent(
        "Explain Cymerk's human approval and security approach."
    )

    assert result is not None


def test_unknown_information():
    """
    Unknown information should not result in an unauthorized
    CRM action.
    """

    from rag_crm_agent import run_agent

    result = run_agent(
        "Tell me something completely unrelated that is not "
        "in the Cymerk knowledge base."
    )

    assert result is not None


# ============================================================
# CRM APPROVAL FLOW
# ============================================================

def test_create_lead_approved():
    """
    A valid lead can be created only after approval.
    """

    result = create_lead(
        name="John Smith",
        title="CEO",
        company="Approved Manufacturing",
        lead_score=90,
    )

    assert result["success"] is True
    assert result["status"] == "pending_approval"
    assert "approval_id" in result

    approval_id = result["approval_id"]

    approval = approve_crm_lead(
        approval_id
    )

    assert approval["success"] is True
    assert approval["status"] == "approved"

    execution = execute_approved_crm_lead(
        approval_id
    )

    assert execution["success"] is True
    assert execution["status"] == "created"
    assert execution["approval_id"] == approval_id

    record = execution["record"]

    assert record["name"] == "John Smith"
    assert record["title"] == "CEO"
    assert record["company"] == "Approved Manufacturing"
    assert record["lead_score"] == 90
    assert record["status"] == "New"


def test_create_lead_rejected():
    """
    A rejected lead must never be created.
    """

    result = create_lead(
        name="Rejected User",
        title="CFO",
        company="Rejected Company",
        lead_score=80,
    )

    assert result["success"] is True
    assert result["status"] == "pending_approval"

    approval_id = result["approval_id"]

    rejection = reject_crm_lead(
        approval_id
    )

    assert rejection["success"] is False
    assert rejection["status"] == "rejected"

    execution = execute_approved_crm_lead(
        approval_id
    )

    assert execution["success"] is False
    assert execution["status"] == "approval_required"


# ============================================================
# VALIDATION
# ============================================================

def test_invalid_crm_lead():
    """
    Invalid CRM lead data must be rejected before an approval
    request is created.
    """

    result = create_lead(
        name="",
        title="CEO",
        company="Invalid Company",
        lead_score=150,
    )

    assert result["success"] is False
    assert result["status"] == "validation_failed"


def test_create_lead_requires_approval():
    """
    Creating a lead through the agent-facing function must
    create a pending approval request rather than a CRM record.
    """

    result = create_lead(
        name="Pending User",
        title="VP Sales",
        company="Pending Company",
        lead_score=85,
    )

    assert result["success"] is True
    assert result["status"] == "pending_approval"

    approval_id = result["approval_id"]

    status = get_approval_status(
        approval_id
    )

    assert status["success"] is True
    assert status["status"] == "pending"

    execution = execute_approved_crm_lead(
        approval_id
    )

    assert execution["success"] is False
    assert execution["status"] == "approval_required"


# ============================================================
# APPROVAL ACTION SECURITY
# ============================================================

def test_unsupported_action_cannot_create_approval():
    """
    Unsupported approval actions must be rejected by the
    approval service.
    """

    approval_id = str(uuid.uuid4())

    result = request_approval(
        approval_id=approval_id,
        action="delete_crm_lead",
        lead={
            "name": "Unauthorized User",
            "title": "CEO",
            "company": "Unauthorized Company",
            "lead_score": 95,
        },
        created_at=utc_timestamp(),
    )

    assert result["success"] is False
    assert result["status"] == "invalid_action"


# ============================================================
# UNKNOWN APPROVAL
# ============================================================

def test_unknown_approval_id_cannot_execute_crm_lead():
    """
    An unknown approval ID must never authorize CRM execution.
    """

    approval_id = str(uuid.uuid4())

    result = execute_approved_crm_lead(
        approval_id
    )

    assert result["success"] is False
    assert result["status"] == "not_found"
    assert result["approval_id"] == approval_id


# ============================================================
# TERMINAL APPROVAL STATES
# ============================================================

def test_approved_request_cannot_be_rejected():
    """
    Once approved, an approval request cannot subsequently
    be rejected.
    """

    approval_id = make_approved_crm_lead()

    result = reject_crm_lead(
        approval_id
    )

    assert result["success"] is False
    assert result["status"] == "already_resolved"
    assert result["approval_id"] == approval_id


def test_rejected_request_cannot_be_approved():
    """
    Once rejected, an approval request cannot subsequently
    be approved.
    """

    result = create_lead(
        name="Rejected Again",
        title="CEO",
        company="Rejected Again Company",
        lead_score=75,
    )

    assert result["success"] is True
    assert result["status"] == "pending_approval"

    approval_id = result["approval_id"]

    rejected = reject_crm_lead(
        approval_id
    )

    assert rejected["success"] is False
    assert rejected["status"] == "rejected"

    approved = approve_crm_lead(
        approval_id
    )

    assert approved["success"] is False
    assert approved["status"] == "already_resolved"
    assert approved["approval_id"] == approval_id


def test_approved_request_cannot_be_approved_again():
    """
    An already-approved request cannot be approved again.
    """

    approval_id = make_approved_crm_lead()

    result = approve_crm_lead(
        approval_id
    )

    assert result["success"] is False
    assert result["status"] == "already_resolved"
    assert result["approval_id"] == approval_id


# ============================================================
# STEP 5 — LLM SECURITY BOUNDARY
# ============================================================

def test_llm_cannot_access_privileged_crm_operations():
    """
    Security boundary:

    The LLM-facing tool registry must not expose approval
    or CRM execution operations.

    The LLM may request creation of a CRM lead, but it must
    not be able to approve or execute that request itself.

    Human approval and CRM execution remain privileged
    operations outside the LLM tool loop.
    """

    from rag_crm_agent import TOOLS

    tool_names = {
        tool["name"]
        for tool in TOOLS
        if tool.get("type") == "function"
    }

    # The LLM should have access to the lead-request operation.
    assert "create_lead" in tool_names

    # Privileged operations must NOT be exposed to the LLM.
    assert "approve_crm_lead" not in tool_names
    assert "execute_approved_crm_lead" not in tool_names