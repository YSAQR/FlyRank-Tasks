"""
Data cleaning functions.

Each function converts a raw extracted string into its clean, typed form.
Invalid or unparseable inputs return ``None`` so the caller can decide
whether to reject the record.

Cleaning rules
--------------
- **Price**: Strip leading currency symbols (``£``, ``$``, ``€``),
  remove commas, convert to ``Decimal`` for monetary precision,
  then to ``float`` for JSON serialisation.
- **Rating**: Map the word used as CSS class (``One`` … ``Five``) to an
  integer 1–5.
- **Availability**: Normalise to one of the allowed values
  (``"in stock"``, ``"out of stock"``).
- **Title**: Strip leading/trailing whitespace.
- **URL**: Resolve relative paths against the base URL to produce an
  absolute ``https://`` URL.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from scraper.config import BASE_URL

# ---------------------------------------------------------------------------
# Rating word → integer mapping
# ---------------------------------------------------------------------------
_RATING_MAP: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

# ---------------------------------------------------------------------------
# Allowed normalised availability values
# ---------------------------------------------------------------------------
_AVAILABILITY_MAP: dict[str, str] = {
    "in stock": "in stock",
    "out of stock": "out of stock",
}

# Regex to strip anything inside parentheses, e.g. "(19 available)"
_PARENS_RE = re.compile(r"\(.*?\)")


def clean_price(raw: str | None) -> float | None:
    """Convert ``'£51.77'`` → ``51.77`` (float).

    Uses ``Decimal`` internally for precision, then converts to ``float``
    because JSON has no Decimal type.

    Returns ``None`` for blank, non-numeric, or negative values.
    """
    if not raw or not raw.strip():
        return None
    # Strip known currency symbols, the Â encoding artifact (UTF-8 £ as
    # Latin-1 produces "Â£"), and whitespace.  Use a regex to extract the
    # first numeric-looking portion.
    cleaned = re.sub(r"^[^\d.-]+", "", raw.strip())
    cleaned = cleaned.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    if value < 0:
        return None
    return float(value)


def clean_rating(raw: str | None) -> int | None:
    """Convert a rating word (``'Three'``) to an integer (``3``).

    The source site encodes ratings as CSS classes like
    ``star-rating Three``.  We accept the word alone.

    Returns ``None`` for unrecognised or blank inputs.
    """
    if not raw or not raw.strip():
        return None
    return _RATING_MAP.get(raw.strip().lower())


def clean_title(raw: str | None) -> str | None:
    """Strip whitespace.  Returns ``None`` for blank strings."""
    if not raw or not raw.strip():
        return None
    return raw.strip()


def clean_availability(raw: str | None) -> str | None:
    """Normalise availability text to ``'in stock'`` or ``'out of stock'``.

    The raw text from the page may look like
    ``'\\n    In stock\\n'`` or ``'In stock (19 available)'``.

    Returns ``None`` if the text cannot be mapped.
    """
    if not raw or not raw.strip():
        return None
    # Remove parenthesised text, collapse whitespace, lowercase.
    text = _PARENS_RE.sub("", raw).strip().lower()
    return _AVAILABILITY_MAP.get(text)


def clean_product_url(raw: str | None, page_url: str | None = None) -> str | None:
    """Resolve a relative product link to an absolute URL.

    ``page_url`` is the URL of the listing page the link was extracted
    from, used as the base for ``urljoin``.  Falls back to ``BASE_URL``
    if not provided.

    Returns ``None`` for blank inputs.
    """
    if not raw or not raw.strip():
        return None
    base = page_url if page_url else BASE_URL
    absolute = urljoin(base, raw.strip())
    return absolute
