from pathlib import Path


def load_document(path):
    """
    Load a text document.
    """
    path = Path(path)

    return path.read_text(
        encoding="utf-8"
    )


def chunk_text(text, max_chars=600):
    """
    Split a document by major sections.

    Each section becomes its own retrieval unit.
    Large sections are further split by paragraphs.
    """

    lines = text.splitlines()

    sections = []
    current_section = []

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        is_heading = (
            stripped in [
                "Company Overview",
                "Core Services",
                "Human Approval",
                "Security",
                "Typical Client Use Cases",
                "Implementation Approach",
            ]
        )

        if is_heading and current_section:

            sections.append(
                "\n\n".join(current_section)
            )

            current_section = []

        current_section.append(stripped)

    if current_section:
        sections.append(
            "\n\n".join(current_section)
        )

    chunks = []

    for section in sections:

        if len(section) <= max_chars:

            chunks.append(section)

            continue

        paragraphs = section.split("\n\n")

        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:

            paragraph_length = len(paragraph)

            if (
                current_chunk
                and current_length + paragraph_length > max_chars
            ):
                chunks.append(
                    "\n\n".join(current_chunk)
                )

                current_chunk = []
                current_length = 0

            current_chunk.append(paragraph)

            current_length += paragraph_length + 2

        if current_chunk:

            chunks.append(
                "\n\n".join(current_chunk)
            )

    return chunks


if __name__ == "__main__":

    document_path = (
        Path(__file__).resolve().parents[1]
        / "documents"
        / "cymerk_company_guide.txt"
    )

    text = load_document(document_path)

    chunks = chunk_text(text)

    print(
        f"Document length: {len(text)} characters"
    )

    print(
        f"Chunks created: {len(chunks)}"
    )

    for index, chunk in enumerate(chunks):

        print("\n" + "=" * 60)
        print(f"CHUNK {index + 1}")
        print("=" * 60)

        print(chunk)