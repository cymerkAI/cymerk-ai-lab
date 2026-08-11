import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = PROJECT_ROOT / "02_rag"

sys.path.insert(0, str(RAG_DIR))

from knowledge_agent import answer_question

EVALUATION_FILE = PROJECT_ROOT / "02_rag" / "evaluations" / "evaluation_cases.json"


def load_evaluation_cases():
    with open(EVALUATION_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["evaluation_cases"]


def evaluate_case(case):
    question = case["question"]
    expected_keywords = case["expected_keywords"]
    expected_behavior = case["expected_behavior"]

    answer = answer_question(question)
    answer_lower = answer.lower()

    if expected_behavior == "unknown":
        passed = "don't have enough information" in answer_lower
    else:
        passed = all(
            keyword.lower() in answer_lower
            for keyword in expected_keywords
        )

    return {
        "id": case["id"],
        "question": question,
        "passed": passed,
        "answer": answer,
    }


def run_evaluation():
    cases = load_evaluation_cases()
    results = []

    print()
    print("=" * 60)
    print("CYMERK AI RAG EVALUATION")
    print("=" * 60)

    for case in cases:
        print()
        print("=" * 60)
        print(f"Evaluating {case['id']}")
        print("=" * 60)

        result = evaluate_case(case)
        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"

        print(f"Question: {result['question']}")
        print(f"Result:   {status}")

        if not result["passed"]:
            print()
            print("AI RESPONSE:")
            print(result["answer"])

    total = len(results)
    passed = sum(result["passed"] for result in results)
    failed = total - passed

    accuracy = passed / total * 100 if total > 0 else 0

    print()
    print("=" * 60)
    print("CYMERK AI EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Cases evaluated: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Accuracy:        {accuracy:.1f}%")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_evaluation()