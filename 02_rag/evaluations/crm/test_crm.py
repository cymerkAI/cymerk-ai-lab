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


def test_valid_lead_approved():
    """
    A valid lead should first enter pending approval,
    then be created after explicit approval.
    """

    request = create_lead(
        name="John Smith",
        title="CEO",
        company="ABC Manufacturing",
        lead_score=90,
        require_approval=True,
    )

    if request.get("status") != "pending_approval":
        print("FAIL: test_valid_lead_approved")
        return False

    approval_id = request.get("approval_id")

    if not approval_id:
        print("FAIL: test_valid_lead_approved")
        return False

    result = approve_crm_lead(approval_id)

    if result.get("success") is True and result.get("status") == "created":
        print("PASS: test_valid_lead_approved")
        return True

    print("FAIL: test_valid_lead_approved")
    return False


def test_valid_lead_rejected():
    """
    A valid lead should NOT be created when human approval
    is explicitly rejected.
    """

    request = create_lead(
        name="Jane Doe",
        title="VP Sales",
        company="XYZ Corporation",
        lead_score=85,
        require_approval=True,
    )

    if request.get("status") != "pending_approval":
        print("FAIL: test_valid_lead_rejected")
        return False

    approval_id = request.get("approval_id")

    if not approval_id:
        print("FAIL: test_valid_lead_rejected")
        return False

    result = reject_crm_lead(approval_id)

    if (
        result.get("success") is False
        and result.get("status") == "rejected"
    ):
        print("PASS: test_valid_lead_rejected")
        return True

    print("FAIL: test_valid_lead_rejected")
    return False


def test_invalid_high_score():
    """
    Lead score must not exceed 100.
    """

    result = create_lead(
        name="Test User",
        title="Manager",
        company="Test Company",
        lead_score=101,
        require_approval=True,
    )

    if result.get("status") == "validation_failed":
        print("PASS: Lead score above 100 rejected")
        return True

    print("FAIL: Lead score above 100 accepted")
    return False


def test_invalid_negative_score():
    """
    Lead score must not be below 0.
    """

    result = create_lead(
        name="Test User",
        title="Manager",
        company="Test Company",
        lead_score=-1,
        require_approval=True,
    )

    if result.get("status") == "validation_failed":
        print("PASS: Negative lead score rejected")
        return True

    print("FAIL: Negative lead score accepted")
    return False


def test_missing_name():
    """
    Lead name cannot be empty.
    """

    result = create_lead(
        name="",
        title="Manager",
        company="Test Company",
        lead_score=50,
        require_approval=True,
    )

    if result.get("status") == "validation_failed":
        print("PASS: Missing name rejected")
        return True

    print("FAIL: Missing name accepted")
    return False


def test_invalid_title():
    """
    Lead title cannot be empty.
    """

    result = create_lead(
        name="Test User",
        title="",
        company="Test Company",
        lead_score=50,
        require_approval=True,
    )

    if result.get("status") == "validation_failed":
        print("PASS: Missing title rejected")
        return True

    print("FAIL: Missing title accepted")
    return False


def main():
    print("=" * 60)
    print("CYMERK CRM EVALUATION")
    print("=" * 60)

    tests = [
        test_valid_lead_approved,
        test_valid_lead_rejected,
        test_invalid_high_score,
        test_invalid_negative_score,
        test_missing_name,
        test_invalid_title,
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
    print("CYMERK CRM EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Cases evaluated: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Accuracy:        {accuracy:.1f}%")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()