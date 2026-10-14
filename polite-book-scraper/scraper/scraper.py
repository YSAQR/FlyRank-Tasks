"""
Orchestrator — ties fetching, parsing, cleaning, validation, and export together.

This module contains the top-level ``run_scraper()`` function that
drives the entire pipeline and returns a structured report dict.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from scraper.cleaners import (
    clean_availability,
    clean_price,
    clean_product_url,
    clean_rating,
    clean_title,
)
from scraper.config import PAGE_URL_TEMPLATE, TARGET_BOOK_COUNT, TARGET_PAGES
from scraper.exporter import export_books, export_report
from scraper.fetcher import FetchResult, PageFetcher
from scraper.models import Book
from scraper.parser import RawBookData, parse_book_listings

logger = logging.getLogger(__name__)


def run_scraper() -> dict[str, Any]:
    """Execute the full scraping pipeline.

    Returns the scrape report dict (also written to disk).
    """
    fetcher = PageFetcher()

    # ------ Phase 1: fetch pages -----------------------------------------
    fetch_results: list[FetchResult] = []
    for page_num in range(1, TARGET_PAGES + 1):
        url = PAGE_URL_TEMPLATE.format(page_number=page_num)
        logger.info("Fetching page %d: %s", page_num, url)
        result = fetcher.fetch(url)
        fetch_results.append(result)
        if result.success:
            logger.info("  [OK] page %d fetched (%d bytes)", page_num,
                        len(result.html or ""))
        else:
            logger.warning("  [FAIL] page %d failed: %s", page_num, result.error)

    pages_fetched = sum(1 for r in fetch_results if r.success)
    failed_pages: list[dict[str, Any]] = [
        {"url": r.url, "error": r.error}
        for r in fetch_results if not r.success
    ]

    # ------ Phase 2: parse + clean + validate ----------------------------
    all_raw: list[tuple[RawBookData, str]] = []  # (raw_data, page_url)
    for result in fetch_results:
        if not result.success or result.html is None:
            continue
        raw_books = parse_book_listings(result.html, result.url)
        for rb in raw_books:
            all_raw.append((rb, result.url))

    total_extracted = len(all_raw)
    logger.info("Extracted %d raw book records from %d pages",
                total_extracted, pages_fetched)

    valid_books: list[Book] = []
    invalid_records: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    duplicate_count = 0

    for raw, page_url in all_raw:
        # --- clean ---
        title = clean_title(raw.title)
        price = clean_price(raw.price)
        rating = clean_rating(raw.rating)
        availability = clean_availability(raw.availability)
        product_url = clean_product_url(raw.product_url, page_url)

        # --- validate ---
        try:
            book = Book(
                title=title,          # type: ignore[arg-type]
                price=price,          # type: ignore[arg-type]
                rating=rating,        # type: ignore[arg-type]
                availability=availability,  # type: ignore[arg-type]
                product_url=product_url,    # type: ignore[arg-type]
            )
        except (ValidationError, TypeError) as exc:
            invalid_records.append({
                "raw_title": raw.title,
                "raw_price": raw.price,
                "raw_rating": raw.rating,
                "raw_availability": raw.availability,
                "raw_product_url": raw.product_url,
                "errors": str(exc),
            })
            continue

        # --- deduplicate ---
        if book.product_url in seen_urls:
            duplicate_count += 1
            logger.debug("Duplicate skipped: %s", book.product_url)
            continue
        seen_urls.add(book.product_url)
        valid_books.append(book)

    logger.info(
        "Validation complete: %d valid, %d invalid, %d duplicates",
        len(valid_books), len(invalid_records), duplicate_count,
    )

    # ------ Phase 3: export ----------------------------------------------
    books_path = export_books(valid_books)
    target_met = len(valid_books) >= TARGET_BOOK_COUNT
    completion_status = "complete" if target_met else "incomplete"

    report: dict[str, Any] = {
        "target_pages": TARGET_PAGES,
        "pages_fetched": pages_fetched,
        "total_extracted": total_extracted,
        "valid_count": len(valid_books),
        "invalid_count": len(invalid_records),
        "duplicate_count": duplicate_count,
        "target_book_count": TARGET_BOOK_COUNT,
        "completion_status": completion_status,
        "books_file": str(books_path),
        "failed_pages": failed_pages,
        "validation_errors": invalid_records[:10],  # cap to avoid huge reports
    }
    report_path = export_report(report)

    logger.info("-" * 50)
    logger.info("Scrape report")
    logger.info("  Target pages     : %d", TARGET_PAGES)
    logger.info("  Pages fetched    : %d", pages_fetched)
    logger.info("  Records extracted: %d", total_extracted)
    logger.info("  Valid books      : %d", len(valid_books))
    logger.info("  Invalid records  : %d", len(invalid_records))
    logger.info("  Duplicates       : %d", duplicate_count)
    logger.info("  Status           : %s", completion_status.upper())
    logger.info("  Books file       : %s", books_path)
    logger.info("  Report file      : %s", report_path)
    logger.info("-" * 50)

    return report
