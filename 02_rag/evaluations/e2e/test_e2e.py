import sys
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "02_rag")
)

from rag_crm_agent import run_agent


def test_knowledge_request():
    question = (
        "When does Cymerk recommend human approval?"
    )

    answer = run_agent(question)

    answer_lower = (
        answer
        .lower()
        .replace("-", " ")
        .replace("-", " ")
        .replace("–", " ")
        .replace("—", " ")
    )

    assert "financial transactions" in answer_lower
    assert "external communications" in answer_lower

    print("PASS: Knowledge request")


def test_security_request():
    question = (
        "What security principle should Cymerk AI "
        "solutions follow?"
    )

    answer = run_agent(question)

    answer_lower = (
        answer
        .lower()
        .replace("-", " ")
    )

    assert "least privilege" in answer_lower

    print("PASS: Security knowledge request")


def test_unknown_request():
    question = (
        "What is Cymerk's office in Tokyo?"
    )

    answer = run_agent(question)

    answer_lower = answer.lower()

    refusal_terms = [
        "don't have",
        "do not have",
        "couldn't find",
        "could not find",
        "not in the knowledge base",
        "no information",
        "cannot find",
        "can't find",
    ]

    assert any(
        term in answer_lower
        for term in refusal_terms
    )

    print("PASS: Unknown information handled safely")


def test_create_lead_approved():
    question = (
        "Create a CRM lead for John Smith, "
        "CEO of ABC Manufacturing, "
        "with a lead score of 90."
    )

    with patch(
        "builtins.input",
        return_value="y"
    ):
        answer = run_agent(question)

    answer_lower = answer.lower()

    assert "john smith" in answer_lower
    assert "abc manufacturing" in answer_lower
    assert "90" in answer_lower

    print("PASS: CRM lead created after approval")


def test_create_lead_rejected():
    question = (
        "Create a CRM lead for Jane Doe, "
        "CFO of XYZ Corporation, "
        "with a lead score of 80."
    )

    with patch(
        "builtins.input",
        return_value="n"
    ):
        answer = run_agent(question)

    answer_lower = answer.lower()

    assert (
        "rejected" in answer_lower
        or "not granted" in answer_lower
    )

    print("PASS: CRM creation rejected without approval")


def test_invalid_lead():
    question = (
        "Create a CRM lead for Test User, "
        "CEO of Test Company, "
        "with a lead score of 150."
    )

    with patch(
        "builtins.input",
        return_value="y"
    ):
        answer = run_agent(question)

    answer_lower = answer.lower()

    assert (
        "validation" in answer_lower
        or "100" in answer_lower
        or "invalid" in answer_lower
    )

    print("PASS: Invalid CRM lead rejected")


def main():
    tests = [
        test_knowledge_request,
        test_security_request,
        test_unknown_request,
        test_create_lead_approved,
        test_create_lead_rejected,
        test_invalid_lead,
    ]

    passed = 0

    print("=" * 60)
    print("CYMERK FULL END-TO-END AGENT EVALUATION")
    print("=" * 60)

    for test in tests:
        try:
            test()
            passed += 1

        except AssertionError:
            print(f"FAIL: {test.__name__}")

        except Exception as error:
            print(f"ERROR: {test.__name__}")
            print(error)

    total = len(tests)

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    print()
    print("=" * 60)
    print("CYMERK END-TO-END EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Cases evaluated: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {total - passed}")
    print(f"Accuracy:        {accuracy:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()