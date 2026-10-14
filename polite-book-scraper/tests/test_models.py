"""Tests for scraper.models (Pydantic validation)."""

import pytest
from pydantic import ValidationError

from scraper.models import Book

VALID_BOOK = {
    "title": "A Light in the Attic",
    "price": 51.77,
    "rating": 3,
    "availability": "in stock",
    "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
}


class TestBookAcceptance:
    def test_valid_book(self):
        book = Book(**VALID_BOOK)
        assert book.title == "A Light in the Attic"
        assert book.price == 51.77
        assert book.rating == 3
        assert book.availability == "in stock"

    def test_out_of_stock_is_valid(self):
        data = {**VALID_BOOK, "availability": "out of stock"}
        book = Book(**data)
        assert book.availability == "out of stock"

    def test_zero_price_is_valid(self):
        data = {**VALID_BOOK, "price": 0.0}
        book = Book(**data)
        assert book.price == 0.0

    def test_rating_boundaries(self):
        for r in (1, 5):
            book = Book(**{**VALID_BOOK, "rating": r})
            assert book.rating == r


class TestBookRejection:
    def test_empty_title(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "title": ""})

    def test_missing_title(self):
        data = {k: v for k, v in VALID_BOOK.items() if k != "title"}
        with pytest.raises(ValidationError):
            Book(**data)

    def test_negative_price(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "price": -1.0})

    def test_price_none(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "price": None})

    def test_rating_zero(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "rating": 0})

    def test_rating_six(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "rating": 6})

    def test_unknown_availability(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "availability": "pre-order"})

    def test_relative_url(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "product_url": "catalogue/book/index.html"})

    def test_empty_url(self):
        with pytest.raises(ValidationError):
            Book(**{**VALID_BOOK, "product_url": ""})
