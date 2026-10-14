"""Tests for scraper.exporter module."""

import json
from pathlib import Path

from scraper.exporter import export_books, export_report
from scraper.models import Book

SAMPLE_BOOK = Book(
    title="Test Book",
    price=19.99,
    rating=4,
    availability="in stock",
    product_url="https://books.toscrape.com/catalogue/test-book_1/index.html",
)


class TestExportBooks:
    def test_writes_valid_json_array(self, tmp_path: Path):
        path = tmp_path / "books.json"
        result = export_books([SAMPLE_BOOK], path=path)
        assert result == path
        assert path.exists()

        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Test Book"
        assert data[0]["price"] == 19.99  # JSON number, not string

    def test_empty_list(self, tmp_path: Path):
        path = tmp_path / "books.json"
        export_books([], path=path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == []

    def test_reload_matches_original(self, tmp_path: Path):
        books = [SAMPLE_BOOK]
        path = tmp_path / "books.json"
        export_books(books, path=path)

        data = json.loads(path.read_text(encoding="utf-8"))
        reloaded = [Book(**record) for record in data]
        assert len(reloaded) == 1
        assert reloaded[0].title == SAMPLE_BOOK.title
        assert reloaded[0].price == SAMPLE_BOOK.price

    def test_multiple_books(self, tmp_path: Path):
        book2 = Book(
            title="Another Book",
            price=5.00,
            rating=1,
            availability="out of stock",
            product_url="https://books.toscrape.com/catalogue/another_2/index.html",
        )
        path = tmp_path / "books.json"
        export_books([SAMPLE_BOOK, book2], path=path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) == 2


class TestExportReport:
    def test_writes_report(self, tmp_path: Path):
        report = {
            "target_pages": 3,
            "pages_fetched": 3,
            "valid_count": 60,
            "completion_status": "complete",
        }
        path = tmp_path / "report.json"
        result = export_report(report, path=path)
        assert result == path

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["valid_count"] == 60
        assert data["completion_status"] == "complete"
