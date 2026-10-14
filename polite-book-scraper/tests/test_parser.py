"""Tests for scraper.parser module.

Uses local HTML fragments instead of live network requests.
"""

from scraper.parser import RawBookData, parse_book_listings

# A minimal product_pod article matching the real site structure.
SINGLE_BOOK_HTML = """
<article class="product_pod">
    <div class="image_container">
        <a href="a-light-in-the-attic_1000/index.html">
            <img src="image.jpg" alt="A Light in the Attic" class="thumbnail">
        </a>
    </div>
    <p class="star-rating Three">
        <i class="icon-star"></i>
    </p>
    <h3><a href="a-light-in-the-attic_1000/index.html"
           title="A Light in the Attic">A Light in the ...</a></h3>
    <div class="product_price">
        <p class="price_color">£51.77</p>
        <p class="instock availability">
            <i class="icon-ok"></i>
            In stock
        </p>
    </div>
</article>
"""

FULL_PAGE_HTML = f"""
<html><body>
<section>
<div><ol class="row">
    <li class="col-xs-6">{SINGLE_BOOK_HTML}</li>
</ol></div>
</section>
</body></html>
"""

MISSING_TITLE_HTML = """
<article class="product_pod">
    <p class="star-rating Two"></p>
    <div class="product_price">
        <p class="price_color">£10.00</p>
        <p class="instock availability">In stock</p>
    </div>
</article>
"""

MISSING_PRICE_HTML = """
<article class="product_pod">
    <p class="star-rating Four"></p>
    <h3><a href="book_1/index.html" title="Some Book">Some Book</a></h3>
    <div class="product_price">
        <p class="instock availability">In stock</p>
    </div>
</article>
"""

NO_ARTICLES_HTML = "<html><body><p>No books here.</p></body></html>"

PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"


class TestParseBookListings:
    def test_single_book_extracts_all_fields(self):
        books = parse_book_listings(FULL_PAGE_HTML, PAGE_URL)
        assert len(books) == 1
        book = books[0]
        assert book.title == "A Light in the Attic"
        assert book.price == "£51.77"
        assert book.rating == "Three"
        assert book.availability is not None
        assert "In stock" in book.availability
        assert book.product_url == "a-light-in-the-attic_1000/index.html"

    def test_no_articles_returns_empty(self):
        books = parse_book_listings(NO_ARTICLES_HTML, PAGE_URL)
        assert books == []

    def test_missing_title_returns_none_title(self):
        html = f"<html><body>{MISSING_TITLE_HTML}</body></html>"
        books = parse_book_listings(html, PAGE_URL)
        assert len(books) == 1
        assert books[0].title is None

    def test_missing_price_returns_none_price(self):
        html = f"<html><body>{MISSING_PRICE_HTML}</body></html>"
        books = parse_book_listings(html, PAGE_URL)
        assert len(books) == 1
        assert books[0].price is None

    def test_multiple_books(self):
        html = f"""<html><body>
        <article class="product_pod">
            <p class="star-rating One"></p>
            <h3><a href="b1/index.html" title="Book One">Book One</a></h3>
            <div class="product_price">
                <p class="price_color">£5.00</p>
                <p class="instock availability">In stock</p>
            </div>
        </article>
        <article class="product_pod">
            <p class="star-rating Five"></p>
            <h3><a href="b2/index.html" title="Book Two">Book Two</a></h3>
            <div class="product_price">
                <p class="price_color">£99.99</p>
                <p class="instock availability">Out of stock</p>
            </div>
        </article>
        </body></html>"""
        books = parse_book_listings(html, PAGE_URL)
        assert len(books) == 2
        assert books[0].title == "Book One"
        assert books[1].title == "Book Two"
