import re
import unicodedata


def normalize_text(text: str) -> str:
    # Normalize unicode (fixes ligatures like ﬁ→fi, ﬀ→ff, etc.)
    text = unicodedata.normalize("NFKC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Rejoin hyphenated line-breaks (common in PDF text extraction)
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Collapse multiple spaces/tabs on a single line
    text = re.sub(r"[ \t]+", " ", text)

    # Remove trailing spaces before newline
    text = re.sub(r"\n[ \t]+", "\n", text)

    # Collapse 3+ consecutive blank lines to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_pages(pages: list[dict]) -> list[dict]:
    normalized_pages = []

    for page in pages:
        text = normalize_text(page["text"])

        normalized_pages.append(
            {
                "page_number": page["page_number"],
                "text": text,
            }
        )

    return normalized_pages