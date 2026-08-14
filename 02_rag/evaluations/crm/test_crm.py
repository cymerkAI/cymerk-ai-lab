import sys
from pathlib import Path

# Allow imports from 02_rag

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from agent_tools import (
    create_lead,
    approve_crm_lead,
    reject_crm_lead,
    execute_approved_crm_lead,
)

from rag_crm_agent import run_agent


# ============================================================
# KNOWLEDGE TESTS
# ============================================================

def test_knowledge_request():
    """
    Basic knowledge retrieval test.
    """

    answer = run_agent(
        "What is Cymerk's implementation approach?"
    )

    assert answer
    assert len(answer.strip()) > 20


def test_security_request():
    """
    Security knowledge request.
    """

    answer = run_agent(
        "What security principle should Cymerk AI solutions follow?"
    )

    assert answer
    assert len(answer.strip()) > 20


def test_unknown_information():
    """
    Agent should safely handle information that is not
    present in the knowledge base.
    """

    answer = run_agent(
        "What is Cymerk's office in Tokyo?"
    )

    answer_lower = answer.lower()

    safe_indicators = [
        "couldn't find",
        "could not find",
        "don't have",
        "do not have",
        "not available",
        "not found",
        "no information",
        "not in the knowledge base",
        "knowledge base does not",
        "cannot find",
    ]

    assert any(
        phrase in answer_lower
        for phrase in safe_indicators
    )


# ============================================================
# APPROVED CRM WORKFLOW
# ============================================================

def test_create_lead_approved():
    """
    Valid CRM lead:

    1. Request approval
    2. Receive approval ID
    3. Approve request
    4. Execute approved CRM action
    5. CRM record is created
    """

    request = create_lead(
        name="John Smith",
        title="CEO",
        company="ABC Manufacturing",
        lead_score=90,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    assert approval_id

    approval = approve_crm_lead(
        approval_id
    )

    assert approval.get("success") is True
    assert approval.get("status") == "approved"

    result = execute_approved_crm_lead(
        approval_id
    )

    assert result.get("success") is True
    assert result.get("status") == "created"

    assert result["record"]["name"] == "John Smith"
    assert result["record"]["company"] == "ABC Manufacturing"
    assert result["record"]["lead_score"] == 90
    assert result["record"]["status"] == "New"


# ============================================================
# REJECTED CRM WORKFLOW
# ============================================================

def test_create_lead_rejected():
    """
    Valid CRM lead:

    1. Request approval
    2. Receive approval ID
    3. Reject request
    4. CRM record must NOT be created
    """

    request = create_lead(
        name="Jane Doe",
        title="CFO",
        company="XYZ Corporation",
        lead_score=80,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    assert approval_id

    result = reject_crm_lead(
        approval_id
    )

    assert result.get("success") is False
    assert result.get("status") == "rejected"

    execution = execute_approved_crm_lead(
        approval_id
    )

    assert execution.get("success") is False
    assert execution.get("status") == "approval_required"


# ============================================================
# INVALID CRM DATA
# ============================================================

def test_invalid_crm_lead():
    """
    Invalid CRM data must be rejected before approval.
    """

    result = create_lead(
        name="",
        title="CEO",
        company="Invalid Company",
        lead_score=150,
    )

    assert result.get("success") is False
    assert result.get("status") == "validation_failed"

    assert "error" in result


# ============================================================
# APPROVAL BYPASS PROTECTION
# ============================================================

def test_create_lead_requires_approval():
    """
    Creating a CRM lead must always create a pending
    approval request.

    There is intentionally no require_approval=False
    bypass anymore.
    """

    request = create_lead(
        name="Security Test User",
        title="CTO",
        company="Security Test Company",
        lead_score=95,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    assert approval_id

    execution = execute_approved_crm_lead(
        approval_id
    )

    assert execution.get("success") is False
    assert execution.get("status") == "approval_required"


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import pytest

    raise SystemExit(
        pytest.main(
            [__file__, "-v"]
        )
    )