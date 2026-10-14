# Polite Book Scraper

A resilient, ethical web scraper built in Python that extracts, cleans, validates, and exports structured book data from [Books to Scrape](https://books.toscrape.com/).

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests: pytest](https://img.shields.io/badge/tests-72%20passed-brightgreen.svg)](tests/)
[![Code Style: Clean & Typed](https://img.shields.io/badge/typing-pydantic%20v2-orange.svg)](scraper/models.py)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Assignment Objectives](#assignment-objectives)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture & Project Structure](#architecture--project-structure)
- [Scraping Ethics & Throttling](#scraping-ethics--throttling)
- [Target Website & Scope](#target-website--scope)
- [Data Schema & Cleaning Rules](#data-schema--cleaning-rules)
- [Example JSON Output](#example-json-output)
- [Installation & Quick Start](#installation--quick-start)
- [Running the Scraper](#running-the-scraper)
- [Running the Automated Tests](#running-the-automated-tests)
- [Output Files & Report](#output-files--report)
- [Verified Execution Results](#verified-execution-results)
- [Error Handling & Reliability](#error-handling--reliability)
- [Limitations](#limitations)
- [GitHub Deployment Instructions](#github-deployment-instructions)

---

## Project Overview

**Polite Book Scraper** is a production-grade Python web scraping pipeline designed to demonstrate professional data harvesting standards:

1. **Polite HTTP Fetching**: Configurable request throttling, custom descriptive `User-Agent`, bounded exponential backoff retry policy, and adherence to `Retry-After` headers.
2. **Robust HTML Parsing**: Clean separation of raw DOM extraction from data normalization using BeautifulSoup4.
3. **Strict Data Cleaning**: Monetary sanitization with Python's `Decimal`, rating word-to-integer mappings, whitespace stripping, and absolute URL resolution.
4. **Schema Validation**: Automated contract enforcement with Pydantic v2 models to reject malformed records before storage.
5. **Deduplication & Reporting**: Stable URL-based deduplication and full diagnostic metadata export.

---

## Assignment Objectives

- Scrape exactly **60 books** across the first **3 catalogue pages** of the target website.
- Convert raw scraped strings into strictly typed and cleaned data.
- Enforce schema validation (ensuring non-empty titles, valid monetary values, 1–5 ratings, normalized availability, and absolute URLs).
- Gracefully handle network issues (timeouts, 404s, 429s, 5xx) and broken markup without crashing.
- Export results into `output/books.json` and execution analytics into `output/scrape_report.json`.
- Maintain a complete automated test suite with mock fixtures (no live server hammering).

---

## Key Features

- **Sequential & Throttled**: Requests are fired sequentially with a default 1.5s polite pause.
- **Resilient Retry Policy**: Bounded retries (default: 3) with exponential backoff (`2^attempt` seconds) on transient failures (`429`, `500`, `502`, `503`, `504`, network timeouts).
- **No-Retry on Permanent Errors**: Immediately flags `404 Not Found` without wasting server resources.
- **Graceful Partial Run Recovery**: A single failed page or malformed record never halts the entire pipeline; available valid records are preserved and saved.
- **Unit & Integration Test Coverage**: 72 tests covering parsing, cleaning edge cases, schema boundary validation, exporter serialization, and network fault injection.

---

## Technology Stack

- **Python**: 3.10+ (tested on Python 3.14)
- **HTTP Client**: [`requests`](https://requests.readthedocs.io/)
- **HTML Parsing**: [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/)
- **Data Validation & Typing**: [`pydantic`](https://docs.pydantic.dev/) v2
- **Testing Framework**: [`pytest`](https://docs.pytest.org/)
- **Standard Library**: `decimal`, `json`, `urllib.parse`, `logging`, `time`, `pathlib`

---

## Architecture & Project Structure

The project strictly follows the Single Responsibility Principle:

```text
polite-book-scraper/
├── .gitignore               # Excludes venvs, caches, .env, output/*.json
├── requirements.txt         # Minimal, pinned dependencies
├── main.py                  # CLI entry point with status exit codes
├── README.md                # Comprehensive project documentation
├── output/
│   ├── .gitkeep             # Preserves output folder in version control
│   ├── books.json           # Validated book records (JSON array)
│   └── scrape_report.json   # Run summary and diagnostics
├── scraper/
│   ├── __init__.py          # Package marker
│   ├── config.py            # Centralized constants, URLs, and retry policies
│   ├── fetcher.py           # Polite HTTP client with backoff and timeouts
│   ├── parser.py            # Raw HTML extraction via BeautifulSoup
│   ├── cleaners.py          # Data cleansing and string-to-type transformations
│   ├── models.py            # Pydantic v2 schemas and field validators
│   ├── exporter.py          # Deterministic JSON export utilities
│   └── scraper.py           # Pipeline orchestrator
└── tests/
    ├── test_cleaners.py      # Unit tests for prices, ratings, URLs, availability
    ├── test_parser.py        # Tests with static HTML fragments
    ├── test_models.py        # Pydantic acceptance and rejection test cases
    ├── test_exporter.py      # Serialization and file writing tests
    └── test_error_handling.py# Mocked network failures, timeouts, and retries
```

---

## Scraping Ethics & Throttling

When scraping public websites, respecting infrastructure and service terms is essential:

1. **Robots.txt Inspection**: The site's `robots.txt` was inspected prior to scraping (returns 404; the platform explicitly welcomes practice scraping).
2. **Identification**: Every request includes an informative `User-Agent`:
   ```text
   PoliteBookScraper/1.0 (+https://github.com/YSAQR/polite-book-scraper; contact: ysaqr111@gmail.com)
   ```
3. **Sequential Execution**: No concurrent threads or asynchronous floods.
4. **Paced Crawling**: An intentional pause (`POLITE_DELAY_SECONDS = 1.5s`) is enforced between page requests.
5. **Timeouts**: Every request defines a strict 10-second timeout to prevent lingering sockets.
6. **Transient Backoff**: If an HTTP 429 or 503 is encountered, backoff respects `Retry-After` headers or backs off exponentially.

---

## Target Website & Scope

- **Target Site**: [Books to Scrape](https://books.toscrape.com/)
- **Target Pages**: 3 pages (`page-1.html`, `page-2.html`, `page-3.html`)
- **Records per Page**: 20 book cards (`article.product_pod`)
- **Target Total**: Exactly 60 books collected and validated.

---

## Data Schema & Cleaning Rules

### Pydantic Model (`scraper.models.Book`)

| Field | Type | Validation Rules |
| :--- | :--- | :--- |
| `title` | `str` | Must not be empty or whitespace-only. |
| `price` | `float` | Must be a non-negative float (`>= 0.0`), cleaned via `Decimal`. |
| `rating` | `int` | Integer bounded between `1` and `5` inclusive. |
| `availability`| `str` | Normalized to `'in stock'` or `'out of stock'`. |
| `product_url` | `str` | Valid absolute URL starting with `http://` or `https://`. |

### Cleaning Transformations (`scraper.cleaners`)

- **Price**: Strips currency signs (`£`, `$`, `€`) and UTF-8 encoding misinterpretation artifacts (`Â£`). Validates decimal precision using `Decimal` before converting to a JSON float.
- **Rating**: Maps textual CSS classes (`One`, `Two`, `Three`, `Four`, `Five`) to integers `1..5`.
- **Availability**: Extracts `"In stock"` or `"Out of stock"`, removes extra whitespace and inventory count suffixes (e.g., `In stock (22 available)` → `in stock`).
- **Product URL**: Resolves relative paths (e.g., `a-light-in-the-attic_1000/index.html`) against `BASE_URL` to create valid absolute links.

---

## Example JSON Output

```json
[
  {
    "title": "A Light in the Attic",
    "price": 51.77,
    "rating": 3,
    "availability": "in stock",
    "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
  },
  {
    "title": "Tipping the Velvet",
    "price": 53.74,
    "rating": 1,
    "availability": "in stock",
    "product_url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"
  }
]
```

---

## Installation & Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YSAQR/polite-book-scraper.git
cd polite-book-scraper
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Scraper

To execute the scraper through the single standard entry point:

```bash
python main.py
```

### Expected Console Output
```text
[INFO] Fetching page 1: https://books.toscrape.com/catalogue/page-1.html
[INFO]   ✓ page 1 fetched (50469 bytes)
[INFO] Fetching page 2: https://books.toscrape.com/catalogue/page-2.html
[INFO]   ✓ page 2 fetched (50877 bytes)
[INFO] Fetching page 3: https://books.toscrape.com/catalogue/page-3.html
[INFO]   ✓ page 3 fetched (51374 bytes)
[INFO] Extracted 60 raw book records from 3 pages
[INFO] Validation complete: 60 valid, 0 invalid, 0 duplicates
[INFO] Exported 60 books to output/books.json
[INFO] Exported scrape report to output/scrape_report.json
--------------------------------------------------
Scrape report
  Target pages     : 3
  Pages fetched    : 3
  Records extracted: 60
  Valid books      : 60
  Invalid records  : 0
  Duplicates       : 0
  Status           : COMPLETE
  Books file       : output/books.json
  Report file      : output/scrape_report.json
--------------------------------------------------
```

### Exit Codes
- `0`: Scraper succeeded and collected all target records (`complete`).
- `1`: Run incomplete or unhandled error encountered (`incomplete` or `failed`).

---

## Running the Automated Tests

All automated tests use static HTML fixtures and mocked HTTP adapters so they execute instantly and never make requests to the live website:

```bash
pytest tests/ -v
```

### Test Coverage Breakdown
- **`tests/test_cleaners.py`** (28 tests): Currency symbols, decimals, thousands commas, encoding artifacts (`Â£`), invalid inputs, rating mappings, availability normalization, and relative-to-absolute URL joins.
- **`tests/test_parser.py`** (5 tests): Single-book extraction, multiple-book parsing, missing tags/attributes, empty markup.
- **`tests/test_models.py`** (13 tests): Valid book models, zero prices, rating boundaries, and rejections for negative prices, ratings outside 1–5, relative URLs, or empty titles.
- **`tests/test_exporter.py`** (5 tests): JSON array formatting, UTF-8 preservation, schema round-trip serialization, report structure.
- **`tests/test_error_handling.py`** (9 tests): Network timeouts, HTTP 404 (no retry), 503 backoff retries, HTTP 429 `Retry-After`, duplicate detection, and partial-run reporting.

---

## Output Files & Report

Execution generates two files in the `output/` directory:

1. **`output/books.json`**: An array of 60 validated book records matching the Pydantic schema.
2. **`output/scrape_report.json`**: Execution diagnostic telemetry:
   ```json
   {
     "target_pages": 3,
     "pages_fetched": 3,
     "total_extracted": 60,
     "valid_count": 60,
     "invalid_count": 0,
     "duplicate_count": 0,
     "target_book_count": 60,
     "completion_status": "complete",
     "books_file": "output/books.json",
     "failed_pages": [],
     "validation_errors": []
   }
   ```

---

## Verified Execution Results

The scraper was executed against the live website and verified:
- **Pages Fetched**: 3 of 3 (`page-1.html`, `page-2.html`, `page-3.html`)
- **Total Raw Records Extracted**: 60
- **Valid Books Collected**: 60 (100% validation success)
- **Invalid Records**: 0
- **Duplicate Records**: 0
- **Final Completion Status**: `complete`
- **Automated Tests**: 72 passed in 0.88s

---

## Error Handling & Reliability

The pipeline isolates failures at multiple levels:
- **Network Level**: Network timeouts and socket disconnects trigger exponential backoff up to 3 retries.
- **HTTP Level**: HTTP 404 is identified as non-retryable and skips to the next page. HTTP 429 checks `Retry-After` headers.
- **Page Level**: If one page fails to load, already-collected data is retained, subsequent pages are processed, and the final report highlights the failed page.
- **Record Level**: An unparseable or schema-violating book record is isolated in the error log without discarding or stopping other records.
- **File System Level**: Output directories are automatically provisioned if missing.

---

## Limitations

- Scrapes the catalogue pagination specifically designed for Books to Scrape. If the site layout changes significantly, the CSS selectors in `scraper/parser.py` will require updates.
- JavaScript rendering is not supported (the target site uses server-rendered HTML; headless browsers like Playwright or Selenium are unnecessary).

---

## GitHub Deployment Instructions

To publish this project to GitHub under your account:

1. Create a new public repository on GitHub named **`polite-book-scraper`**:
   - Go to [https://github.com/new](https://github.com/new)
   - Repository name: `polite-book-scraper`
   - Visibility: **Public**
   - Do **NOT** initialize with a README, .gitignore, or license (these already exist locally).

2. Link your local repository to GitHub and push:
   ```bash
   cd d:\trib\polite-book-scraper
   git remote add origin https://github.com/YSAQR/polite-book-scraper.git
   git branch -M main
   git push -u origin main
   ```

3. Verify the published repository at:
   `https://github.com/YSAQR/polite-book-scraper`
