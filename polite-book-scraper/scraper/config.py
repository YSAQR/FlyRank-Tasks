"""
Scraper configuration constants.

All tunable parameters are centralised here so they are easy to find
and modify without touching application logic.
"""

# ---------------------------------------------------------------------------
# Target website
# ---------------------------------------------------------------------------
BASE_URL = "https://books.toscrape.com/"

# Pages to scrape (the catalogue listing pages).
# Page 1 is also accessible at /catalogue/page-1.html.
PAGE_URL_TEMPLATE = BASE_URL + "catalogue/page-{page_number}.html"

TARGET_PAGES = 3          # Number of listing pages to fetch.
EXPECTED_BOOKS_PER_PAGE = 20
TARGET_BOOK_COUNT = TARGET_PAGES * EXPECTED_BOOKS_PER_PAGE  # 60

# ---------------------------------------------------------------------------
# Polite request settings
# ---------------------------------------------------------------------------
USER_AGENT = (
    "PoliteBookScraper/1.0 "
    "(+https://github.com/student-project; educational-scraper; "
    "contact: student@example.com)"
)

REQUEST_TIMEOUT_SECONDS = 15        # Per-request HTTP timeout.
REQUEST_DELAY_SECONDS = 1.5         # Delay between consecutive requests.

# ---------------------------------------------------------------------------
# Retry policy (for transient failures: network errors, 429, 5xx)
# ---------------------------------------------------------------------------
MAX_RETRIES = 3                     # Maximum retry attempts per page.
RETRY_BACKOFF_FACTOR = 2.0          # Exponential back-off multiplier.
RETRY_INITIAL_WAIT = 1.0            # Seconds before the first retry.

# HTTP status codes that are worth retrying.
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
