import sys
from pathlib import Path

# Allow imports from 02_rag
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from agent_tools import (
    create_lead,
    approve_crm_lead,
    reject_crm_lead,
    execute_approved_crm_lead,
)

from rag_crm_agent import run_agent


def test_knowledge_request():
    """Basic knowledge retrieval test."""

    answer = run_agent(
        "What is Cymerk's implementation approach?"
    )

    assert answer
    assert len(answer.strip()) > 20


def test_security_request():
    """Security knowledge request."""

    answer = run_agent(
        "What security principle should Cymerk AI solutions follow?"
    )

    assert answer
    assert len(answer.strip()) > 20


def test_unknown_information():
    """Agent should safely handle unknown information."""

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


def test_create_lead_approved():
    """Valid CRM lead should be created after approval."""

    request = create_lead(
        name="John Smith",
        title="CEO",
        company="ABC Manufacturing",
        lead_score=90,
    )

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

def test_crm_execution_requires_approval():
    """CRM execution must not occur before human approval."""

    request = create_lead(
        name="Approval Test",
        title="CEO",
        company="Approval Test Company",
        lead_score=95,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    assert approval_id

    result = execute_approved_crm_lead(
        approval_id
    )

    assert result.get("success") is False
    assert result.get("status") == "approval_required"

def test_create_lead_rejected():
    """Valid CRM lead should not be created after rejection."""

    request = create_lead(
        name="Jane Doe",
        title="CFO",
        company="XYZ Corporation",
        lead_score=80,
    
    )

    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    assert approval_id

    result = reject_crm_lead(approval_id)

    assert result.get("success") is False
    assert result.get("status") == "rejected"


def test_invalid_crm_lead():
    """Invalid CRM data must be rejected."""

    result = create_lead(
        name="",
        title="CEO",
        company="Invalid Company",
        lead_score=150,
  
    )

    assert result.get("status") == "validation_failed"