import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from chunker import load_document, chunk_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = (
    PROJECT_ROOT
    / "01_llm_foundations"
    / "01_first_llm_app"
    / ".env"
)

load_dotenv(ENV_FILE)

client = OpenAI()


DOCUMENT_PATH = (
    PROJECT_ROOT
    / "02_rag"
    / "documents"
    / "cymerk_company_guide.txt"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "02_rag"
    / "retrieval"
    / "embeddings.json"
)


def create_embeddings(chunks):
    """
    Create an embedding for every document chunk.
    """

    records = []

    for index, chunk in enumerate(chunks):

        print(f"Creating embedding {index + 1}/{len(chunks)}...")

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk,
        )

        records.append(
            {
                "chunk_id": index,
                "text": chunk,
                "embedding": response.data[0].embedding,
            }
        )

    return records


if __name__ == "__main__":

    text = load_document(DOCUMENT_PATH)

    chunks = chunk_text(text)

    records = create_embeddings(chunks)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(records),
        encoding="utf-8",
    )

    print()
    print("Embedding generation complete.")
    print(f"Chunks embedded: {len(records)}")
    print(f"Saved to: {OUTPUT_PATH}")