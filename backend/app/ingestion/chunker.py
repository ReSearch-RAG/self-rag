import re


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using a simple regex heuristic.
    Handles common abbreviations poorly but avoids requiring NLTK/spacy.
    """
    # Split after . ! ? followed by whitespace and an uppercase letter or end-of-string
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"\'(])", text)
    return [p.strip() for p in parts if p.strip()]


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split a block of text into overlapping character-based chunks,
    preferring sentence boundaries where possible.
    """
    if len(text) <= chunk_size:
        return [text]

    sentences = _split_sentences(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        # If adding this sentence stays within budget, accumulate it
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = (current + " " + sentence).strip() if current else sentence
        else:
            # Flush current chunk
            if current:
                chunks.append(current)
            # If the sentence itself is too long, fall back to hard character split
            if len(sentence) > chunk_size:
                start = 0
                while start < len(sentence):
                    end = start + chunk_size
                    chunks.append(sentence[start:end].strip())
                    start = end - overlap
                current = ""
            else:
                # Start a new chunk, optionally carrying over overlap text
                if chunks:
                    # carry overlap from the end of the previous chunk
                    prev = chunks[-1]
                    carry = prev[-overlap:] if len(prev) > overlap else prev
                    current = (carry + " " + sentence).strip()
                else:
                    current = sentence

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    chunks: list[dict] = []

    for page in pages:
        text = page["text"].strip()

        if not text:
            continue

        # Split on paragraph boundaries first
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

        for paragraph in paragraphs:
            sub_chunks = _chunk_text(paragraph, chunk_size, overlap)
            for sub in sub_chunks:
                chunks.append(
                    {
                        "text": sub,
                        "page_number": page["page_number"],
                        "section": None,  # Section detection requires PDF structure metadata
                    }
                )

    return chunks