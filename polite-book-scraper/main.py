#!/usr/bin/env python3
"""
Polite Book Scraper — entry point.

Usage:
    python main.py

Scrapes the first 3 pages of https://books.toscrape.com/, cleans and
validates each record, and exports the results to ``output/books.json``
and ``output/scrape_report.json``.

Exit codes:
    0 — target met (≥ 60 valid books collected).
    1 — scraping completed but target not met or a runtime error occurred.
"""

from __future__ import annotations

import logging
import sys

from scraper.scraper import run_scraper


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    try:
        report = run_scraper()
    except Exception:
        logging.exception("Fatal error during scraping")
        return 1

    if report.get("completion_status") == "complete":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
