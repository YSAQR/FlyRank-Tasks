"""
HTML parser for the Books to Scrape catalogue listing pages.

Extracts raw book data from a page's HTML.  All values are returned
as raw strings; cleaning and validation happen in later stages.

The parser is isolated so it can be tested with local HTML fixtures
without making network requests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


@dataclass
class RawBookData:
    """Container for data extracted straight from the HTML.

    All fields are optional strings because any element might be
    missing or malformed.
    """

    title: str | None = None
    price: str | None = None
    rating: str | None = None
    availability: str | None = None
    product_url: str | None = None


def parse_book_listings(html: str, page_url: str) -> list[RawBookData]:
    """Parse a catalogue page and return a list of ``RawBookData``.

    Parameters
    ----------
    html:
        The full HTML content of one listing page.
    page_url:
        The URL the HTML was fetched from (used for resolving relative
        links later — stored as-is here).

    Returns
    -------
    list[RawBookData]
        One entry per ``<article class="product_pod">`` found on the
        page.  Empty list if none are found.
    """
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.product_pod")

    if not articles:
        logger.warning("No book articles found on %s", page_url)
        return []

    books: list[RawBookData] = []
    for article in articles:
        books.append(_extract_one(article))
    return books


def _extract_one(article: Tag) -> RawBookData:
    """Extract raw fields from a single ``<article class="product_pod">``."""
    return RawBookData(
        title=_extract_title(article),
        price=_extract_price(article),
        rating=_extract_rating(article),
        availability=_extract_availability(article),
        product_url=_extract_product_url(article),
    )


# ---------------------------------------------------------------------------
# Per-field extraction helpers
# ---------------------------------------------------------------------------

def _extract_title(article: Tag) -> str | None:
    """Get the full title from ``<h3><a title="...">``."""
    h3 = article.select_one("h3")
    if h3 is None:
        return None
    anchor = h3.select_one("a")
    if anchor is None:
        return None
    # The ``title`` attribute holds the full, untruncated title.
    return anchor.get("title") or anchor.get_text(strip=True) or None


def _extract_price(article: Tag) -> str | None:
    """Get the raw price string from ``<p class="price_color">``."""
    tag = article.select_one("p.price_color")
    return tag.get_text(strip=True) if tag else None


def _extract_rating(article: Tag) -> str | None:
    """Get the rating word from the CSS class ``star-rating <Word>``."""
    tag = article.select_one("p.star-rating")
    if tag is None:
        return None
    # Classes look like ``['star-rating', 'Three']``.
    classes = tag.get("class", [])
    for cls in classes:
        if cls.lower() != "star-rating":
            return cls  # e.g. "Three"
    return None


def _extract_availability(article: Tag) -> str | None:
    """Get the availability text from ``<p class="instock availability">``."""
    tag = article.select_one("p.availability")
    return tag.get_text(strip=True) if tag else None


def _extract_product_url(article: Tag) -> str | None:
    """Get the relative product URL from the first ``<a href="...">``."""
    h3 = article.select_one("h3")
    if h3 is None:
        return None
    anchor = h3.select_one("a")
    if anchor is None:
        return None
    href = anchor.get("href")
    return href if href else None
