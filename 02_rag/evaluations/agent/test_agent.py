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

TEST_CASES = [
    (
        "Human approval policy",
        "When does Cymerk recommend human approval?",
        ["human approval", "approval", "human"],
    ),
(
    "Security principle",
    "What security principle should Cymerk AI solutions follow?",
    [
        "least-privilege",
        "least privilege",
        "only the tools",
        "required for their assigned tasks",
    ],
),
    (
        "Implementation approach",
        "What is Cymerk's implementation approach?",
        [
            "discover",
            "workflow",
            "automation",
            "design",
            "build",
            "test",
            "approval",
            "deploy",
        ],
    ),
    (
        "Client use cases",
        "What are some typical Cymerk client use cases?",
        ["automation", "workflow", "ai"],
    ),
]


UNKNOWN_QUESTION = "What is Cymerk's office in Tokyo?"


SAFE_UNKNOWN_INDICATORS = [
    "not available",
    "not found",
    "couldn't find",
    "could not find",
    "don't have",
    "do not have",
    "no information",
    "not in the knowledge base",
    "information is not available",
    "not available in the knowledge base",
    "not present in the knowledge base",
    "cannot find",
    "can't find",
    "unable to find",
]


def evaluate_case(name, question, expected_terms):
    print()
    print("=" * 60)
    print(f"Evaluating: {name}")
    print("=" * 60)
    print(f"Question: {question}")

    try:
        answer = run_agent(question)
    except Exception as error:
        print("Result:   FAIL")
        print()
        print("ERROR:")
        print(error)
        return False

    if answer is None:
        print("Result:   FAIL")
        print()
        print("AI RESPONSE:")
        print("None")
        return False

    answer_text = str(answer).strip()
    answer_lower = answer_text.lower()

    for term in expected_terms:
        if term.lower() in answer_lower:
            print("Result:   PASS")
            return True

    print("Result:   FAIL")
    print()
    print("AI RESPONSE:")
    print(answer_text)

    return False


def evaluate_unknown_information():
    print()
    print("=" * 60)
    print("Evaluating: Unknown information")
    print("=" * 60)
    print(f"Question: {UNKNOWN_QUESTION}")

    try:
        answer = run_agent(UNKNOWN_QUESTION)
    except Exception as error:
        print("Result:   FAIL")
        print()
        print("ERROR:")
        print(error)
        return False

    if answer is None:
        print("Result:   FAIL")
        print()
        print("AI RESPONSE:")
        print("None")
        return False

    answer_text = str(answer).strip()
    answer_lower = answer_text.lower()

    for indicator in SAFE_UNKNOWN_INDICATORS:
        if indicator in answer_lower:
            print("Result:   PASS")
            return True

    print("Result:   FAIL")
    print()
    print("AI RESPONSE:")
    print(answer_text)

    return False


def main():
    print()
    print("=" * 60)
    print("CYMERK AI AGENT EVALUATION")
    print("=" * 60)

    passed = 0
    failed = 0
    total = 0

    for name, question, expected_terms in TEST_CASES:
        total += 1

        result = evaluate_case(
            name,
            question,
            expected_terms,
        )

        if result:
            passed += 1
        else:
            failed += 1

    total += 1

    result = evaluate_unknown_information()

    if result:
        passed += 1
    else:
        failed += 1

    if total > 0:
        accuracy = (passed / total) * 100
    else:
        accuracy = 0.0

    print()
    print("=" * 60)
    print("CYMERK AI AGENT EVALUATION")
    print("=" * 60)
    print(f"Cases evaluated: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Accuracy:        {accuracy:.1f}%")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()