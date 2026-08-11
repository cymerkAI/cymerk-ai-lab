import sys
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "02_rag")
)

from agent_tools import create_lead


def test_valid_lead_approved():
    with patch(
        "builtins.input",
        return_value="y"
    ):
        result = create_lead(
            name="John Smith",
            title="CEO",
            company="ABC Manufacturing",
            lead_score=90,
        )

    assert result["success"] is True
    assert result["status"] == "created"
    assert result["record"]["name"] == "John Smith"
    assert result["record"]["company"] == "ABC Manufacturing"
    assert result["record"]["lead_score"] == 90

    print("PASS: Valid lead approved")


def test_valid_lead_rejected():
    with patch(
        "builtins.input",
        return_value="n"
    ):
        result = create_lead(
            name="Jane Doe",
            title="CFO",
            company="XYZ Corporation",
            lead_score=80,
        )

    assert result["success"] is False
    assert result["status"] == "rejected"

    print("PASS: Human rejection prevents creation")


def test_invalid_lead_score_high():
    with patch(
        "builtins.input",
        return_value="y"
    ):
        result = create_lead(
            name="Test User",
            title="CEO",
            company="Test Company",
            lead_score=101,
        )

    assert result["success"] is False
    assert result["status"] == "validation_failed"

    print("PASS: Lead score above 100 rejected")


def test_invalid_lead_score_low():
    with patch(
        "builtins.input",
        return_value="y"
    ):
        result = create_lead(
            name="Test User",
            title="CEO",
            company="Test Company",
            lead_score=-1,
        )

    assert result["success"] is False
    assert result["status"] == "validation_failed"

    print("PASS: Negative lead score rejected")


def test_missing_name():
    with patch(
        "builtins.input",
        return_value="y"
    ):
        result = create_lead(
            name="",
            title="CEO",
            company="Test Company",
            lead_score=75,
        )

    assert result["success"] is False
    assert result["status"] == "validation_failed"

    print("PASS: Missing name rejected")


def test_missing_company():
    with patch(
        "builtins.input",
        return_value="y"
    ):
        result = create_lead(
            name="Test User",
            title="CEO",
            company="",
            lead_score=75,
        )

    assert result["success"] is False
    assert result["status"] == "validation_failed"

    print("PASS: Missing company rejected")


def main():
    tests = [
        test_valid_lead_approved,
        test_valid_lead_rejected,
        test_invalid_lead_score_high,
        test_invalid_lead_score_low,
        test_missing_name,
        test_missing_company,
    ]

    passed = 0

    print("=" * 60)
    print("CYMERK CRM TOOL EVALUATION")
    print("=" * 60)

    for test in tests:
        try:
            test()
            passed += 1

        except AssertionError as error:
            print(f"FAIL: {test.__name__}")
            print(error)

        except Exception as error:
            print(f"ERROR: {test.__name__}")
            print(error)

    total = len(tests)

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    print("=" * 60)
    print("CYMERK CRM EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Cases evaluated: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {total - passed}")
    print(f"Accuracy:        {accuracy:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()