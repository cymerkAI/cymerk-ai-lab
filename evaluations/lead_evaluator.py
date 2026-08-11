import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from lead_cases import LEAD_CASES


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = (
    PROJECT_ROOT
    / "01_llm_foundations"
    / "01_first_llm_app"
    / ".env"
)

load_dotenv(ENV_FILE)

client = OpenAI()


def evaluate_lead(case):
    """
    Ask the LLM to classify a lead.
    """

    prompt = f"""
You are a B2B sales lead qualification analyst.

Analyze the following lead.

Name: {case["name"]}
Title: {case["title"]}
Company: {case["company"]}
Location: {case["location"]}
Interest: {case["interest"]}

Classify the lead as exactly one of:

high
medium
low

Return ONLY valid JSON in this format:

{{
    "priority": "high"
}}
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    text = response.output_text.strip()

    return json.loads(text)


def run_evaluation():

    results = []

    for case in LEAD_CASES:

        print("\n" + "=" * 60)
        print(f"Evaluating {case['id']}")
        print("=" * 60)

        prediction = evaluate_lead(case)

        actual = prediction["priority"]
        expected = case["expected_priority"]

        passed = actual == expected

        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"Result:   {'PASS' if passed else 'FAIL'}")

        results.append(
            {
                "id": case["id"],
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )

    total = len(results)
    passed = sum(
        result["passed"]
        for result in results
    )

    accuracy = passed / total

    print("\n")
    print("=" * 60)
    print("CYMERK AI EVALUATION")
    print("=" * 60)

    print(f"Cases evaluated: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {total - passed}")
    print(f"Accuracy:        {accuracy:.1%}")


if __name__ == "__main__":
    run_evaluation()