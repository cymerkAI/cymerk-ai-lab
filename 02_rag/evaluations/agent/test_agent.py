import sys
from pathlib import Path

# ============================================================
# PATH SETUP
# ============================================================

CURRENT_FILE = Path(__file__).resolve()

RAG_ROOT = CURRENT_FILE.parents[2]

if str(RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ROOT))

# ============================================================
# IMPORT AGENT
# ============================================================

from rag_crm_agent import run_agent


# ============================================================
# HUMAN APPROVAL
# ============================================================

def test_human_approval_policy():
    answer = run_agent(
        "When does Cymerk recommend human approval?"
    )

    assert answer is not None

    answer_lower = str(answer).lower()

    assert any(
        term in answer_lower
        for term in [
            "human approval",
            "approval",
            "human",
        ]
    )


# ============================================================
# SECURITY
# ============================================================

def test_security_principle():
    answer = run_agent(
        "What security principle should Cymerk AI solutions follow?"
    )

    assert answer is not None

    answer_lower = str(answer).lower()

    assert any(
        term in answer_lower
        for term in [
            "least-privilege",
            "least privilege",
            "only the tools",
            "required for their assigned tasks",
        ]
    )


# ============================================================
# IMPLEMENTATION APPROACH
# ============================================================

def test_implementation_approach():
    answer = run_agent(
        "What is Cymerk's implementation approach?"
    )

    assert answer is not None

    answer_lower = str(answer).lower()

    assert any(
        term in answer_lower
        for term in [
            "discover",
            "workflow",
            "automation",
            "design",
            "build",
            "test",
            "approval",
            "deploy",
        ]
    )


# ============================================================
# CLIENT USE CASES
# ============================================================

def test_client_use_cases():
    answer = run_agent(
        "What are some typical Cymerk client use cases?"
    )

    assert answer is not None

    answer_lower = str(answer).lower()

    assert any(
        term in answer_lower
        for term in [
            "automation",
            "workflow",
            "ai",
        ]
    )


# ============================================================
# UNKNOWN INFORMATION
# ============================================================

def test_unknown_information():
    answer = run_agent(
        "What is Cymerk's office in Tokyo?"
    )

    assert answer is not None

    answer_lower = str(answer).lower()

    assert any(
        indicator in answer_lower
        for indicator in [
            "not available",
            "not found",
            "couldn't find",
            "could not find",
            "no information",
            "not in the knowledge base",
            "information is not available",
        ]
    )
def test_unknown_tool_is_blocked_by_permission_layer():
    """
    An unregistered tool must be denied by the permission
    layer rather than executed by the agent.
    """

    from permissions import check_tool_permission

    result = check_tool_permission(
        "definitely_not_a_real_tool"
    )

    assert result["allowed"] is False
    assert result["reason"] == "Tool is not authorized."

def test_agent_blocks_unauthorized_tool(monkeypatch):
    """
    The agent must not execute a tool when the permission
    layer denies that tool.
    """

    import rag_crm_agent

    executed = {
        "value": False
    }

    def fake_permission(tool_name):
        return {
            "allowed": False,
            "requires_approval": False,
            "reason": "Tool is not authorized.",
        }

    def fake_create_lead(**kwargs):
        executed["value"] = True

        return (
            '{"success": true, "status": "created"}'
        )

    monkeypatch.setattr(
        rag_crm_agent,
        "check_tool_permission",
        fake_permission,
    )

    monkeypatch.setattr(
        rag_crm_agent,
        "create_lead_tool",
        fake_create_lead,
    )

    class FakeToolCall:
        type = "function_call"
        name = "create_lead"
        arguments = "{}"
        call_id = "test-call"

    class FirstResponse:
        output = [
            FakeToolCall()
        ]
        id = "test-response"

    class FinalResponse:
        output = []
        output_text = (
            "The requested tool is not authorized."
        )

    class FakeClient:
        class responses:

            call_count = 0

            @staticmethod
            def create(**kwargs):

                FakeClient.responses.call_count += 1

                if FakeClient.responses.call_count == 1:
                    return FirstResponse()

                return FinalResponse()

    monkeypatch.setattr(
        rag_crm_agent,
        "client",
        FakeClient(),
    )

    result = rag_crm_agent.run_agent(
        "Create a CRM lead."
    )

    assert executed["value"] is False

    assert (
        result
        == "The requested tool is not authorized."
    )