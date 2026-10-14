"""Tests for scraper.cleaners module."""

from scraper.cleaners import (
    clean_availability,
    clean_price,
    clean_product_url,
    clean_rating,
    clean_title,
)


# ── clean_price ─────────────────────────────────────────────────────────────

class TestCleanPrice:
    def test_gbp_symbol(self):
        assert clean_price("£51.77") == 51.77

    def test_dollar_symbol(self):
        assert clean_price("$29.99") == 29.99

    def test_euro_symbol(self):
        assert clean_price("€10.00") == 10.0

    def test_no_symbol(self):
        assert clean_price("35.50") == 35.50

    def test_comma_thousands(self):
        assert clean_price("£1,001.99") == 1001.99

    def test_zero_price(self):
        assert clean_price("£0.00") == 0.0

    def test_whitespace_padding(self):
        assert clean_price("  £51.77  ") == 51.77

    def test_negative_price_returns_none(self):
        assert clean_price("-5.00") is None

    def test_empty_string_returns_none(self):
        assert clean_price("") is None

    def test_none_returns_none(self):
        assert clean_price(None) is None

    def test_garbage_returns_none(self):
        assert clean_price("free") is None

    def test_only_symbol_returns_none(self):
        assert clean_price("£") is None

    def test_multiple_dots_returns_none(self):
        assert clean_price("£12.34.56") is None

    def test_encoding_artifact_symbol(self):
        assert clean_price("Â£51.77") == 51.77


# ── clean_rating ────────────────────────────────────────────────────────────

class TestCleanRating:
    def test_one(self):
        assert clean_rating("One") == 1

    def test_five(self):
        assert clean_rating("Five") == 5

    def test_lowercase(self):
        assert clean_rating("three") == 3

    def test_mixed_case(self):
        assert clean_rating("TWO") == 2

    def test_whitespace(self):
        assert clean_rating("  Four  ") == 4

    def test_unknown_word(self):
        assert clean_rating("Six") is None

    def test_empty(self):
        assert clean_rating("") is None

    def test_none(self):
        assert clean_rating(None) is None

    def test_numeric_string(self):
        assert clean_rating("3") is None  # must be word form


# ── clean_title ─────────────────────────────────────────────────────────────

class TestCleanTitle:
    def test_normal(self):
        assert clean_title("A Light in the Attic") == "A Light in the Attic"

    def test_strips_whitespace(self):
        assert clean_title("  Hello  ") == "Hello"

    def test_empty(self):
        assert clean_title("") is None

    def test_whitespace_only(self):
        assert clean_title("   ") is None

    def test_none(self):
        assert clean_title(None) is None


# ── clean_availability ──────────────────────────────────────────────────────

class TestCleanAvailability:
    def test_in_stock(self):
        assert clean_availability("In stock") == "in stock"

    def test_in_stock_with_count(self):
        assert clean_availability("In stock (19 available)") == "in stock"

    def test_whitespace_around(self):
        assert clean_availability("\n    In stock\n") == "in stock"

    def test_out_of_stock(self):
        assert clean_availability("Out of stock") == "out of stock"

    def test_unknown(self):
        assert clean_availability("Pre-order") is None

    def test_empty(self):
        assert clean_availability("") is None

    def test_none(self):
        assert clean_availability(None) is None


# ── clean_product_url ───────────────────────────────────────────────────────

class TestCleanProductUrl:
    def test_relative_from_catalogue_page(self):
        result = clean_product_url(
            "a-light-in-the-attic_1000/index.html",
            "https://books.toscrape.com/catalogue/page-1.html",
        )
        assert result == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

    def test_already_absolute(self):
        url = "https://books.toscrape.com/catalogue/some-book/index.html"
        assert clean_product_url(url) == url

    def test_relative_with_catalogue_prefix(self):
        result = clean_product_url(
            "../catalogue/book_1/index.html",
            "https://books.toscrape.com/catalogue/page-1.html",
        )
        assert result == "https://books.toscrape.com/catalogue/book_1/index.html"

    def test_empty(self):
        assert clean_product_url("") is None

    def test_none(self):
        assert clean_product_url(None) is None
