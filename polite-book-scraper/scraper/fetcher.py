"""
HTTP fetcher with polite behaviour.

Responsibilities:
- Sequential, throttled HTTP GET requests.
- Descriptive User-Agent header.
- Bounded retry with exponential back-off for transient failures.
- Respect for Retry-After headers.
- Clear error reporting (never silently swallows failures).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import requests

from scraper.config import (
    MAX_RETRIES,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    RETRY_BACKOFF_FACTOR,
    RETRY_INITIAL_WAIT,
    RETRYABLE_STATUS_CODES,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Outcome of a single page fetch."""

    url: str
    success: bool
    status_code: int | None = None
    html: str | None = None
    error: str | None = None


@dataclass
class PageFetcher:
    """Fetches pages sequentially with polite delays and bounded retries."""

    delay: float = REQUEST_DELAY_SECONDS
    _last_request_time: float = field(default=0.0, init=False, repr=False)

    # ----- public API -------------------------------------------------------

    def fetch(self, url: str) -> FetchResult:
        """Fetch a single URL, retrying on transient errors.

        Returns a ``FetchResult`` regardless of success or failure;
        never raises for HTTP/network issues.
        """
        self._throttle()

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                self._last_request_time = time.monotonic()

                # Permanent client errors — do NOT retry.
                if response.status_code == 404:
                    logger.warning("Page not found (404): %s", url)
                    return FetchResult(url=url, success=False,
                                       status_code=404,
                                       error="HTTP 404 Not Found")

                # Retryable server / rate-limit errors.
                if response.status_code in RETRYABLE_STATUS_CODES:
                    wait = self._retry_wait(response, attempt)
                    logger.warning(
                        "HTTP %d from %s — retry %d/%d in %.1fs",
                        response.status_code, url, attempt, MAX_RETRIES, wait,
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(wait)
                        continue
                    return FetchResult(
                        url=url, success=False,
                        status_code=response.status_code,
                        error=f"HTTP {response.status_code} after "
                              f"{MAX_RETRIES} retries",
                    )

                # Any other non-2xx we did not anticipate — fail immediately.
                if not (200 <= response.status_code < 300):
                    logger.warning("Unexpected HTTP %d: %s",
                                   response.status_code, url)
                    return FetchResult(
                        url=url, success=False,
                        status_code=response.status_code,
                        error=f"Unexpected HTTP {response.status_code}",
                    )

                # Success.
                return FetchResult(url=url, success=True,
                                   status_code=response.status_code,
                                   html=response.text)

            except requests.ConnectionError as exc:
                wait = self._backoff_wait(attempt)
                logger.warning("Connection error for %s — retry %d/%d in "
                               "%.1fs: %s", url, attempt, MAX_RETRIES,
                               wait, exc)
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    continue
                return FetchResult(url=url, success=False,
                                   error=f"Connection error after "
                                         f"{MAX_RETRIES} retries: {exc}")

            except requests.Timeout:
                wait = self._backoff_wait(attempt)
                logger.warning("Timeout for %s — retry %d/%d in %.1fs",
                               url, attempt, MAX_RETRIES, wait)
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    continue
                return FetchResult(url=url, success=False,
                                   error=f"Timeout after {MAX_RETRIES} "
                                         f"retries")

            except requests.RequestException as exc:
                # Catch-all for other request problems; do not retry.
                logger.error("Request failed for %s: %s", url, exc)
                return FetchResult(url=url, success=False,
                                   error=f"Request error: {exc}")

        # Should not be reachable, but safety net.
        return FetchResult(url=url, success=False,
                           error="Exhausted retries (unexpected code path)")

    # ----- internal helpers -------------------------------------------------

    def _throttle(self) -> None:
        """Wait until at least ``self.delay`` seconds since the last request."""
        if self._last_request_time == 0.0:
            return  # First request — no need to wait.
        elapsed = time.monotonic() - self._last_request_time
        remaining = self.delay - elapsed
        if remaining > 0:
            logger.debug("Throttling %.2fs before next request", remaining)
            time.sleep(remaining)

    @staticmethod
    def _retry_wait(response: requests.Response, attempt: int) -> float:
        """Compute wait time, respecting Retry-After if present."""
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return max(float(retry_after), 0.5)
            except ValueError:
                pass
        return RETRY_INITIAL_WAIT * (RETRY_BACKOFF_FACTOR ** (attempt - 1))

    @staticmethod
    def _backoff_wait(attempt: int) -> float:
        return RETRY_INITIAL_WAIT * (RETRY_BACKOFF_FACTOR ** (attempt - 1))
