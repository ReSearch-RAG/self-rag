import re


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n[ \t]+", "\n", text)

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