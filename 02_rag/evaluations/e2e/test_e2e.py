import json
import sys
from pathlib import Path

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
    create_lead,
    approve_crm_lead,
    reject_crm_lead,
    execute_approved_crm_lead,
)

from rag_crm_agent import run_agent


# ============================================================
# HELPERS
# ============================================================

def load_audit_events(log_file: Path):
    """
    Load all valid JSON audit events from the audit log.

    Empty lines are ignored.
    """

    if not log_file.exists():
        return []

    events = []

    with log_file.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            events.append(
                json.loads(line)
            )

    return events


# ============================================================
# KNOWLEDGE / RAG
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
    available in the Cymerk knowledge base.
    """

    answer = run_agent(
        "What is Cymerk's office in Tokyo?"
    )

    assert answer

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
# CRM APPROVAL FLOW
# ============================================================

def test_create_lead_approved():
    """
    A valid CRM lead must:

        1. Create a pending approval request.
        2. Require human approval.
        3. Allow execution only after approval.
        4. Produce a CRM record after approved execution.
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
    assert result.get("approval_id") == approval_id

    record = result.get("record")

    assert record is not None
    assert record["name"] == "John Smith"
    assert record["title"] == "CEO"
    assert record["company"] == "ABC Manufacturing"
    assert record["lead_score"] == 90
    assert record["status"] == "New"


def test_crm_execution_requires_approval():
    """
    CRM execution must not occur before human approval.
    """

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
    """
    A valid CRM lead must not be created after rejection.
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

    rejection = reject_crm_lead(
        approval_id
    )

    assert rejection.get("success") is False
    assert rejection.get("status") == "rejected"

    execution = execute_approved_crm_lead(
        approval_id
    )

    assert execution.get("success") is False
    assert execution.get("status") == "approval_required"


# ============================================================
# CRM VALIDATION
# ============================================================

def test_invalid_crm_lead():
    """
    Invalid CRM data must be rejected before an approval
    request is created.
    """

    result = create_lead(
        name="",
        title="CEO",
        company="Invalid Company",
        lead_score=150,
    )

    assert result.get("success") is False
    assert result.get("status") == "validation_failed"


# ============================================================
# CRM AUDIT SECURITY
# ============================================================

def test_crm_created_audit_event_requires_approved_execution():
    """
    CRM creation must produce exactly one crm_created audit
    event only after the corresponding approval has been granted
    and the approved action has actually executed.

    The test also verifies that attempting execution while the
    request is pending does not create the crm_created event.
    """

    log_file = (
        Path(__file__).resolve().parents[2]
        / "logs"
        / "agent_audit.jsonl"
    )

    # --------------------------------------------------------
    # CREATE PENDING APPROVAL
    # --------------------------------------------------------

    request = create_lead(
        name="Audit Test User",
        title="CEO",
        company="Audit Test Company",
        lead_score=92,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    assert approval_id

    # --------------------------------------------------------
    # EXECUTION MUST BE BLOCKED WHILE PENDING
    # --------------------------------------------------------

    blocked = execute_approved_crm_lead(
        approval_id
    )

    assert blocked.get("success") is False
    assert blocked.get("status") == "approval_required"

    # --------------------------------------------------------
    # VERIFY NO CRM CREATION EVENT WAS CREATED
    # WHILE THE REQUEST WAS STILL PENDING
    # --------------------------------------------------------

    events_before_approval = load_audit_events(
        log_file
    )

    pending_crm_events = [
        event
        for event in events_before_approval
        if (
            event.get("event_type") == "crm_created"
            and event.get("details", {}).get(
                "approval_id"
            ) == approval_id
        )
    ]

    assert pending_crm_events == []

    # --------------------------------------------------------
    # APPROVE REQUEST
    # --------------------------------------------------------

    approval = approve_crm_lead(
        approval_id
    )

    assert approval.get("success") is True
    assert approval.get("status") == "approved"

    # --------------------------------------------------------
    # EXECUTE AFTER APPROVAL
    # --------------------------------------------------------

    result = execute_approved_crm_lead(
        approval_id
    )

    assert result.get("success") is True
    assert result.get("status") == "created"
    assert result.get("approval_id") == approval_id

    # --------------------------------------------------------
    # AUDIT LOG MUST EXIST
    # --------------------------------------------------------

    assert log_file.exists()

    events = load_audit_events(
        log_file
    )

    # --------------------------------------------------------
    # FIND CRM CREATION EVENTS FOR THIS APPROVAL
    # --------------------------------------------------------

    crm_events = [
        event
        for event in events
        if (
            event.get("event_type") == "crm_created"
            and event.get("details", {}).get(
                "approval_id"
            ) == approval_id
        )
    ]

    # Exactly one CRM creation event must exist.
    assert len(crm_events) == 1

    crm_event = crm_events[0]

    # --------------------------------------------------------
    # VERIFY AUDIT EVENT
    # --------------------------------------------------------

    assert crm_event["status"] == "success"

    details = crm_event["details"]

    assert details["approval_id"] == approval_id
    assert details["action"] == "create_crm_lead"
    assert details["company"] == "Audit Test Company"
    assert details["lead_score"] == 92


# ============================================================
# APPROVAL TERMINAL-STATE SECURITY
# ============================================================

def test_approved_request_cannot_be_rejected():
    """
    Once approved, an approval request must not be rejected.
    """

    request = create_lead(
        name="Approved Audit User",
        title="CEO",
        company="Approved Audit Company",
        lead_score=90,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    approval = approve_crm_lead(
        approval_id
    )

    assert approval.get("success") is True
    assert approval.get("status") == "approved"

    rejection = reject_crm_lead(
        approval_id
    )

    assert rejection.get("success") is False
    assert rejection.get("status") == "already_resolved"
    assert rejection.get("approval_id") == approval_id


def test_rejected_request_cannot_be_approved():
    """
    Once rejected, an approval request must not subsequently
    be approved.
    """

    request = create_lead(
        name="Rejected Audit User",
        title="CFO",
        company="Rejected Audit Company",
        lead_score=70,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    rejection = reject_crm_lead(
        approval_id
    )

    assert rejection.get("success") is False
    assert rejection.get("status") == "rejected"

    approval = approve_crm_lead(
        approval_id
    )

    assert approval.get("success") is False
    assert approval.get("status") == "already_resolved"
    assert approval.get("approval_id") == approval_id


def test_approved_request_cannot_be_approved_again():
    """
    An already-approved request cannot be approved again.
    """

    request = create_lead(
        name="Duplicate Approval User",
        title="CEO",
        company="Duplicate Approval Company",
        lead_score=88,
    )

    assert request.get("success") is True
    assert request.get("status") == "pending_approval"

    approval_id = request.get("approval_id")

    first_approval = approve_crm_lead(
        approval_id
    )

    assert first_approval.get("success") is True
    assert first_approval.get("status") == "approved"

    second_approval = approve_crm_lead(
        approval_id
    )

    assert second_approval.get("success") is False
    assert second_approval.get("status") == "already_resolved"
    assert second_approval.get("approval_id") == approval_id


# ============================================================
# UNKNOWN APPROVAL SECURITY
# ============================================================

def test_unknown_approval_id_cannot_execute_crm_lead():
    """
    An unknown approval ID must never authorize CRM execution.
    """

    import uuid

    approval_id = str(
        uuid.uuid4()
    )

    result = execute_approved_crm_lead(
        approval_id
    )

    assert result.get("success") is False
    assert result.get("status") == "not_found"
    assert result.get("approval_id") == approval_id