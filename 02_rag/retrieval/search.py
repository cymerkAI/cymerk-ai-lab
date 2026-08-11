import json
import math
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = (
    PROJECT_ROOT
    / "01_llm_foundations"
    / "01_first_llm_app"
    / ".env"
)

load_dotenv(ENV_FILE)

client = OpenAI()


EMBEDDINGS_PATH = (
    PROJECT_ROOT
    / "02_rag"
    / "retrieval"
    / "embeddings.json"
)


def cosine_similarity(vector_a, vector_b):
    """
    Calculate cosine similarity between two vectors.
    """

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (
        magnitude_a * magnitude_b
    )


def load_embeddings():
    """
    Load stored document embeddings.
    """

    return json.loads(
        EMBEDDINGS_PATH.read_text(
            encoding="utf-8"
        )
    )


def keyword_boost(query, text):
    """
    Add a small relevance boost when important
    query terms appear in a document chunk.
    """

    query_lower = query.lower()
    text_lower = text.lower()

    boost = 0.0

    if "use case" in query_lower or "use cases" in query_lower:
        if "typical client use cases" in text_lower:
            boost += 0.20

    if "service" in query_lower or "services" in query_lower:
        if "core services" in text_lower:
            boost += 0.20

    if "implementation" in query_lower:
        if "implementation approach" in text_lower:
            boost += 0.20

    if "confidential" in query_lower:
        if "confidential information" in text_lower:
            boost += 0.20

    if "security" in query_lower:
        if "security" in text_lower:
            boost += 0.15

    if "human approval" in query_lower:
        if "human approval" in text_lower:
            boost += 0.15

    return boost


def search(query, top_k=2, min_score=0.55):
    """
    Search document chunks using semantic similarity
    plus a small lexical relevance boost.
    """

    records = load_embeddings()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )

    query_embedding = response.data[0].embedding

    results = []

    for record in records:

        semantic_score = cosine_similarity(
            query_embedding,
            record["embedding"],
        )

        boost = keyword_boost(
            query,
            record["text"],
        )

        final_score = semantic_score + boost

        results.append(
            {
                "chunk_id": record["chunk_id"],
                "text": record["text"],
                "score": final_score,
                "semantic_score": semantic_score,
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    filtered_results = [
        result
        for result in results
        if result["score"] >= min_score
    ]

    return filtered_results[:top_k]


if __name__ == "__main__":

    question = input(
        "\nAsk the Cymerk knowledge base: "
    )

    results = search(question)

    print("\n" + "=" * 60)
    print("SEARCH RESULTS")
    print("=" * 60)

    for result in results:

        print(
            f"\nChunk: {result['chunk_id']}"
        )

        print(
            f"Similarity: {result['score']:.4f}"
        )

        print(
            f"Semantic score: "
            f"{result['semantic_score']:.4f}"
        )

        print(
            "\n" + result["text"]
        )
