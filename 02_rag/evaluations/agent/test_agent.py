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