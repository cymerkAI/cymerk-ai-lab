from pathlib import Path
import sys

# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = PROJECT_ROOT / "02_rag"

sys.path.insert(0, str(RAG_DIR))


# ---------------------------------------------------------
# Cymerk RAG imports
# ---------------------------------------------------------

from retrieval.search import search
from knowledge_agent import answer_question


# ---------------------------------------------------------
# Test 1 — Human approval retrieval
# ---------------------------------------------------------

def test_human_approval_retrieval():

    results = search(
        "When does Cymerk recommend human approval?",
        top_k=2,
        min_score=0.55,
    )

    assert len(results) > 0

    combined_text = " ".join(
        result["text"]
        for result in results
    ).lower()

    assert "human approval" in combined_text
    assert "financial transactions" in combined_text


# ---------------------------------------------------------
# Test 2 — Security retrieval
# ---------------------------------------------------------

def test_security_retrieval():

    results = search(
        "What security principle should Cymerk AI solutions follow?",
        top_k=2,
        min_score=0.55,
    )

    assert len(results) > 0

    combined_text = " ".join(
        result["text"]
        for result in results
    ).lower()

    assert "least-privilege" in combined_text


# ---------------------------------------------------------
# Test 3 — Services retrieval
# ---------------------------------------------------------

def test_services_retrieval():

    results = search(
        "What services does Cymerk provide?",
        top_k=2,
        min_score=0.55,
    )

    assert len(results) > 0

    combined_text = " ".join(
        result["text"]
        for result in results
    ).lower()

    assert "ai agent development" in combined_text
    assert "workflow automation" in combined_text


# ---------------------------------------------------------
# Test 4 — Unknown information
# ---------------------------------------------------------

def test_unknown_question():

    answer = answer_question(
        "What is Cymerk's office in Tokyo?"
    )

    assert (
        "don't have enough information"
        in answer.lower()
    )


# ---------------------------------------------------------
# Test 5 — Human approval answer
# ---------------------------------------------------------

def test_human_approval_answer():

    answer = answer_question(
        "When does Cymerk recommend human approval?"
    )

    answer_lower = answer.lower()

    assert "human approval" in answer_lower
    assert "financial transactions" in answer_lower


# ---------------------------------------------------------
# Test 6 — Security answer
# ---------------------------------------------------------

def test_security_answer():

    answer = answer_question(
        "What security principle should Cymerk AI solutions follow?"
    )

    assert "least-privilege" in answer.lower()