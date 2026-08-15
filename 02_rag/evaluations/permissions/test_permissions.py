import sys
from pathlib import Path

# Allow imports from 02_rag
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from permissions import check_tool_permission


def test_search_knowledge_is_allowed():
    """
    Knowledge search is an authorized tool and does not
    require human approval.
    """

    result = check_tool_permission(
        "search_knowledge"
    )

    assert result["allowed"] is True
    assert result["requires_approval"] is False


def test_create_lead_requires_approval():
    """
    CRM lead creation is authorized but requires
    human approval.
    """

    result = check_tool_permission(
        "create_lead"
    )

    assert result["allowed"] is True
    assert result["requires_approval"] is True


def test_approve_crm_lead_is_allowed():
    """
    Approval resolution is an authorized operation.
    """

    result = check_tool_permission(
        "approve_crm_lead"
    )

    assert result["allowed"] is True
    assert result["requires_approval"] is False


def test_reject_crm_lead_is_allowed():
    """
    Rejection resolution is an authorized operation.
    """

    result = check_tool_permission(
        "reject_crm_lead"
    )

    assert result["allowed"] is True
    assert result["requires_approval"] is False


def test_execute_approved_crm_lead_is_allowed():
    """
    Approved CRM execution is an authorized operation.
    """

    result = check_tool_permission(
        "execute_approved_crm_lead"
    )

    assert result["allowed"] is True
    assert result["requires_approval"] is False


def test_unknown_tool_is_denied():
    """
    Tools not registered in the permission registry
    must be denied.
    """

    result = check_tool_permission(
        "unknown_tool"
    )

    assert result["allowed"] is False
    assert result["requires_approval"] is False
    assert result["reason"] == "Tool is not authorized."