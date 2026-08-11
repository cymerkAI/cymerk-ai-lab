import sys
from pathlib import Path

# Allow imports from 02_rag
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from agent_tools import (
    create_lead,
    approve_crm_lead,
    reject_crm_lead,
)


def test_knowledge_request():
    """
    Basic knowledge retrieval test.
    """

    from rag_crm_agent import run_agent

    answer = run_agent(
        "What is Cymerk's implementation approach?"
    )

    if answer and len(answer.strip()) > 20:
        print("PASS: Knowledge request")
        return True

    print("FAIL: Knowledge request")
    return False


def test_security_request():
    """
    Security knowledge request.
    """

    from rag_crm_agent import run_agent

    answer = run_agent(
        "What security principle should Cymerk AI solutions follow?"
    )

    if answer and len(answer.strip()) > 20:
        print("PASS: Security knowledge request")
        return True

    print("FAIL: Security knowledge request")
    return False


def test_unknown_information():
    """
    Agent should safely handle information that is not
    present in the knowledge base.
    """

    from rag_crm_agent import run_agent

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

    if any(
        phrase in answer_lower
        for phrase in safe_indicators
    ):
        print(
            "PASS: Unknown information handled safely"
        )
        return True

    print(
        "FAIL: Unknown information handled safely"
    )
    return False


def test_create_lead_approved():
    """
    Valid CRM lead:
        1. Request approval
        2. Receive approval ID
        3. Approve request
        4. CRM record is created
    """

    request = create_lead(
        name="John Smith",
        title="CEO",
        company="ABC Manufacturing",
        lead_score=90,
        require_approval=True,
    )

    if request.get("status") != "pending_approval":
        print("FAIL: test_create_lead_approved")
        return False

    approval_id = request.get("approval_id")

    if not approval_id:
        print("FAIL: test_create_lead_approved")
        return False

    result = approve_crm_lead(
        approval_id
    )

    if (
        result.get("success") is True
        and result.get("status") == "created"
    ):
        print(
            "PASS: CRM lead created after approval"
        )
        return True

    print(
        "FAIL: CRM lead created after approval"
    )
    return False


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
        require_approval=True,
    )

    if request.get("status") != "pending_approval":
        print("FAIL: test_create_lead_rejected")
        return False

    approval_id = request.get("approval_id")

    if not approval_id:
        print("FAIL: test_create_lead_rejected")
        return False

    result = reject_crm_lead(
        approval_id
    )

    if (
        result.get("success") is False
        and result.get("status") == "rejected"
    ):
        print(
            "PASS: CRM creation rejected without approval"
        )
        return True

    print(
        "FAIL: CRM creation rejected without approval"
    )
    return False


def test_invalid_crm_lead():
    """
    Invalid CRM data must be rejected before approval.
    """

    result = create_lead(
        name="",
        title="CEO",
        company="Invalid Company",
        lead_score=150,
        require_approval=True,
    )

    if result.get("status") == "validation_failed":
        print(
            "PASS: Invalid CRM lead rejected"
        )
        return True

    print(
        "FAIL: Invalid CRM lead rejected"
    )
    return False


def main():

    print("=" * 60)
    print(
        "CYMERK FULL END-TO-END AGENT EVALUATION"
    )
    print("=" * 60)

    tests = [
        test_knowledge_request,
        test_security_request,
        test_unknown_information,
        test_create_lead_approved,
        test_create_lead_rejected,
        test_invalid_crm_lead,
    ]

    passed = 0
    failed = 0

    for test in tests:

        try:

            if test():
                passed += 1
            else:
                failed += 1

        except Exception as error:

            failed += 1

            print(
                f"FAIL: {test.__name__}"
            )

            print(
                f"ERROR: {error}"
            )

    total = len(tests)

    accuracy = (
        (passed / total) * 100
        if total
        else 0
    )

    print()
    print("=" * 60)
    print(
        "CYMERK END-TO-END EVALUATION SUMMARY"
    )
    print("=" * 60)
    print(
        f"Cases evaluated: {total}"
    )
    print(
        f"Passed:          {passed}"
    )
    print(
        f"Failed:          {failed}"
    )
    print(
        f"Accuracy:        {accuracy:.1f}%"
    )
    print("=" * 60)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()