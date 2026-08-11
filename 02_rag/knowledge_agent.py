from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from retrieval.search import search


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = (
    PROJECT_ROOT
    / "01_llm_foundations"
    / "01_first_llm_app"
    / ".env"
)

load_dotenv(ENV_FILE)

client = OpenAI()


def answer_question(question):
    """
    Answer a question using retrieved Cymerk knowledge.
    """

    results = search(
        question,
        top_k=2,
        min_score=0.55,
    )

    if not results:
        return (
            "I don't have enough information in the "
            "Cymerk knowledge base to answer that."
        )

    context_parts = []

    for result in results:
        context_parts.append(
            f"[Source {result['chunk_id']}]\n"
            f"{result['text']}"
        )

    context = "\n\n".join(context_parts)

    response = client.responses.create(
        model="gpt-5-mini",

        instructions="""
You are the Cymerk AI Knowledge Assistant.

Answer the user's question using ONLY the
provided Cymerk knowledge context.

Rules:

1. Do not invent information.
2. If the context does not contain enough
   information to answer the question, say:
   "I don't have enough information in the
   Cymerk knowledge base to answer that."
3. Keep the answer concise and useful.
4. Cite only the source numbers that actually
   support your answer.
""",

        input=f"""
CYMERK KNOWLEDGE CONTEXT:

{context}

USER QUESTION:

{question}
""",
    )

    return response.output_text


if __name__ == "__main__":

    question = input(
        "\nAsk the Cymerk Knowledge Assistant: "
    )

    answer = answer_question(question)

    print("\n" + "=" * 60)
    print("CYMERK AI KNOWLEDGE ASSISTANT")
    print("=" * 60)

    print("\n" + answer)