import logging
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> list[dict]:
    reader = PdfReader(file_path)

    pages = []
    empty_pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if not text.strip():
            empty_pages.append(page_number)

        pages.append(
            {
                "page_number": page_number,
                "text": text,
            }
        )

    if empty_pages:
        logger.warning(
            "Pages with no extractable text in %s: %s. "
            "These may be scanned/image pages.",
            Path(file_path).name,
            empty_pages,
        )

    return pages
