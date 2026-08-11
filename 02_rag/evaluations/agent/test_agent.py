import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "02_rag")
)

from rag_crm_agent import run_agent


def normalize_text(text):
    return (
        text.lower()
        .replace("-", " ")
        .replace("-", " ")
        .replace("–", " ")
        .replace("—", " ")
        .replace("’", "'")
    )


def evaluate_case(name, question, expected_terms):
    print("=" * 60)
    print(f"Evaluating: {name}")
    print("=" * 60)

    answer = run_agent(question)

    answer_lower = normalize_text(answer)

    passed = all(
        normalize_text(term) in answer_lower
        for term in expected_terms
    )

    print(f"Question: {question}")
    print(f"Result:   {'PASS' if passed else 'FAIL'}")

    if not passed:
        print("\nAI RESPONSE:")
        print(answer)

    print()

    return passed
    print("=" * 60)
    print(f"Evaluating: {name}")
    print("=" * 60)

    answer = run_agent(question)

    answer_lower = (
        answer
        .lower()
        .replace("-", " ")
    )

    passed = all(
        term.lower().replace("-", " ") in answer_lower
        for term in expected_terms
    )

    print(f"Question: {question}")
    print(f"Result:   {'PASS' if passed else 'FAIL'}")

    if not passed:
        print("\nAI RESPONSE:")
        print(answer)

    print()

    return passed


def evaluate_unknown_case():
    print("=" * 60)
    print("Evaluating: Unknown information")
    print("=" * 60)

    question = "What is Cymerk's office in Tokyo?"

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

    passed = any(
        term in answer_lower
        for term in refusal_terms
    )

    print(f"Question: {question}")
    print(f"Result:   {'PASS' if passed else 'FAIL'}")

    if not passed:
        print("\nAI RESPONSE:")
        print(answer)

    print()

    return passed


def main():
    cases = [
        {
            "name": "Human approval policy",
            "question": "When does Cymerk recommend human approval?",
            "expected_terms": [
                "financial transactions",
                "customer record changes",
                "external communications",
            ],
        },
        {
            "name": "Security principle",
            "question": (
                "What security principle should Cymerk "
                "AI solutions follow?"
            ),
            "expected_terms": [
                "least privilege",
            ],
        },
        {
            "name": "Implementation approach",
            "question": "What is Cymerk's implementation approach?",
            "expected_terms": [
                "discover the business problem",
                "map the existing workflow",
                "deploy and monitor",
            ],
        },
        {
            "name": "Client use cases",
            "question": (
                "What are some typical Cymerk client use cases?"
            ),
            "expected_terms": [
                "lead qualification",
                "crm automation",
                "customer support",
                "research automation",
            ],
        },
    ]

    passed = 0

    for case in cases:
        if evaluate_case(
            case["name"],
            case["question"],
            case["expected_terms"],
        ):
            passed += 1

    if evaluate_unknown_case():
        passed += 1

    total = len(cases) + 1

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    print("=" * 60)
    print("CYMERK AI AGENT EVALUATION")
    print("=" * 60)
    print(f"Cases evaluated: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {total - passed}")
    print(f"Accuracy:        {accuracy:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()