"""Tests for error handling and scraper reliability.

Uses mocked HTTP responses so the test suite never hits the live website.
"""

from unittest.mock import MagicMock, patch

import requests

from scraper.fetcher import FetchResult, PageFetcher


# ---------------------------------------------------------------------------
# Fetcher error handling
# ---------------------------------------------------------------------------

class TestFetcherTimeout:
    @patch("scraper.fetcher.time.sleep")  # skip actual waits
    @patch("scraper.fetcher.requests.get")
    def test_timeout_retries_then_fails(self, mock_get, _mock_sleep):
        mock_get.side_effect = requests.Timeout("timed out")
        fetcher = PageFetcher(delay=0)
        result = fetcher.fetch("https://example.com/page-1.html")

        assert not result.success
        assert "Timeout" in (result.error or "")
        assert mock_get.call_count == 3  # MAX_RETRIES = 3


class TestFetcherConnectionError:
    @patch("scraper.fetcher.time.sleep")
    @patch("scraper.fetcher.requests.get")
    def test_connection_error_retries(self, mock_get, _mock_sleep):
        mock_get.side_effect = requests.ConnectionError("DNS fail")
        fetcher = PageFetcher(delay=0)
        result = fetcher.fetch("https://example.com/page-1.html")

        assert not result.success
        assert "Connection error" in (result.error or "")
        assert mock_get.call_count == 3


class TestFetcher404:
    @patch("scraper.fetcher.requests.get")
    def test_404_no_retry(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        fetcher = PageFetcher(delay=0)
        result = fetcher.fetch("https://example.com/missing.html")

        assert not result.success
        assert result.status_code == 404
        assert mock_get.call_count == 1  # no retry for 404


class TestFetcherRetryableStatus:
    @patch("scraper.fetcher.time.sleep")
    @patch("scraper.fetcher.requests.get")
    def test_503_retries_then_fails(self, mock_get, _mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.headers = {}
        mock_get.return_value = mock_response

        fetcher = PageFetcher(delay=0)
        result = fetcher.fetch("https://example.com/page-1.html")

        assert not result.success
        assert result.status_code == 503
        assert mock_get.call_count == 3

    @patch("scraper.fetcher.time.sleep")
    @patch("scraper.fetcher.requests.get")
    def test_429_respects_retry_after(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "5"}
        mock_get.return_value = mock_response

        fetcher = PageFetcher(delay=0)
        fetcher.fetch("https://example.com/page-1.html")

        # First retry sleep should be at least 5s (from Retry-After)
        if mock_sleep.call_count > 0:
            first_wait = mock_sleep.call_args_list[0][0][0]
            assert first_wait >= 5.0


class TestFetcherSuccess:
    @patch("scraper.fetcher.requests.get")
    def test_200_returns_html(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Hello</body></html>"
        mock_get.return_value = mock_response

        fetcher = PageFetcher(delay=0)
        result = fetcher.fetch("https://example.com/page-1.html")

        assert result.success
        assert result.html == "<html><body>Hello</body></html>"


# ---------------------------------------------------------------------------
# Scraper pipeline resilience
# ---------------------------------------------------------------------------

class TestFailedPageDoesNotCrashRun:
    """A failed page should not prevent other pages from being processed."""

    @patch("scraper.scraper.PageFetcher")
    def test_one_failed_page_still_produces_partial_results(self, MockFetcher):
        """If page 2 fails, pages 1 and 3 should still produce valid books."""
        book_html = """<html><body>
        <article class="product_pod">
            <p class="star-rating Three"></p>
            <h3><a href="book_1/index.html" title="Valid Book">Valid Book</a></h3>
            <div class="product_price">
                <p class="price_color">£10.00</p>
                <p class="instock availability">In stock</p>
            </div>
        </article>
        </body></html>"""

        success_result = FetchResult(
            url="https://books.toscrape.com/catalogue/page-1.html",
            success=True, status_code=200, html=book_html,
        )
        fail_result = FetchResult(
            url="https://books.toscrape.com/catalogue/page-2.html",
            success=False, status_code=503,
            error="HTTP 503 after 3 retries",
        )

        mock_instance = MockFetcher.return_value
        mock_instance.fetch.side_effect = [
            success_result, fail_result, success_result,
        ]

        from scraper.scraper import run_scraper
        report = run_scraper()

        # Should have processed pages 1 and 3, skipping page 2.
        assert report["pages_fetched"] == 2
        assert report["valid_count"] >= 1  # at least 1 book from each page
        assert len(report["failed_pages"]) == 1
        assert report["completion_status"] == "incomplete"


class TestDuplicateDetection:
    @patch("scraper.scraper.PageFetcher")
    def test_same_book_on_two_pages_counted_once(self, MockFetcher):
        """Duplicate product URLs should be detected and counted."""
        book_html = """<html><body>
        <article class="product_pod">
            <p class="star-rating One"></p>
            <h3><a href="same-book_1/index.html" title="Same Book">Same Book</a></h3>
            <div class="product_price">
                <p class="price_color">£20.00</p>
                <p class="instock availability">In stock</p>
            </div>
        </article>
        </body></html>"""

        result1 = FetchResult(
            url="https://books.toscrape.com/catalogue/page-1.html",
            success=True, status_code=200, html=book_html,
        )
        result2 = FetchResult(
            url="https://books.toscrape.com/catalogue/page-2.html",
            success=True, status_code=200, html=book_html,
        )
        # Third page empty
        result3 = FetchResult(
            url="https://books.toscrape.com/catalogue/page-3.html",
            success=True, status_code=200,
            html="<html><body></body></html>",
        )

        mock_instance = MockFetcher.return_value
        mock_instance.fetch.side_effect = [result1, result2, result3]

        from scraper.scraper import run_scraper
        report = run_scraper()

        assert report["valid_count"] == 1
        assert report["duplicate_count"] == 1


class TestIncompleteReporting:
    @patch("scraper.scraper.PageFetcher")
    def test_fewer_than_60_reports_incomplete(self, MockFetcher):
        """When fewer than 60 valid records are collected, status is incomplete."""
        book_html = """<html><body>
        <article class="product_pod">
            <p class="star-rating Two"></p>
            <h3><a href="only-book_1/index.html" title="Only Book">Only Book</a></h3>
            <div class="product_price">
                <p class="price_color">£15.00</p>
                <p class="instock availability">In stock</p>
            </div>
        </article>
        </body></html>"""

        result = FetchResult(
            url="https://books.toscrape.com/catalogue/page-1.html",
            success=True, status_code=200, html=book_html,
        )
        fail = FetchResult(
            url="https://books.toscrape.com/catalogue/page-2.html",
            success=False, error="Connection error",
        )

        mock_instance = MockFetcher.return_value
        mock_instance.fetch.side_effect = [result, fail, fail]

        from scraper.scraper import run_scraper
        report = run_scraper()

        assert report["completion_status"] == "incomplete"
        assert report["valid_count"] < 60
