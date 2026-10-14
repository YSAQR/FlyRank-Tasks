"""
JSON exporter.

Writes validated book records and a scrape report to the ``output/``
directory.

Output files
------------
- ``output/books.json``  — JSON array of validated book records.
- ``output/scrape_report.json`` — run summary with counts and status.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from scraper.models import Book

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def export_books(books: list[Book], path: Path | None = None) -> Path:
    """Write validated books to a JSON file.

    Returns the path that was written.
    """
    target = path or (OUTPUT_DIR / "books.json")
    target.parent.mkdir(parents=True, exist_ok=True)

    data = [book.model_dump() for book in books]
    target.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Exported %d books to %s", len(books), target)
    return target


def export_report(report: dict[str, Any], path: Path | None = None) -> Path:
    """Write the scrape report to a JSON file.

    Returns the path that was written.
    """
    target = path or (OUTPUT_DIR / "scrape_report.json")
    target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Exported scrape report to %s", target)
    return target
