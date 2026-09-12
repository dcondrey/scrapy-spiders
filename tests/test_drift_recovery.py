"""Prove recovery from markup drift, rather than asserting it in a docstring.

Each test takes a real captured page and mutates it the way a redesign would:
renaming CSS classes, changing the URL scheme, or both. The spider must still
find the listings. Base markup is real (see fixtures/PROVENANCE.md); only the
mutation is synthetic, and the mutation is the thing under test.
"""

import re

from scrapy.http import HtmlResponse, XmlResponse

from scrapyspiders.base import ResilientListingSpider
from scrapyspiders.discovery import feed_entry_links, feed_urls, infer_listing_patterns
from scrapyspiders.extract import discover_links
from scrapyspiders.spiders.entertainmentcareers import EntertainmentcareersSpider

EC_URL = "https://www.entertainmentcareers.net/psearch/?zoom_query=film+editor"
PATTERN = EntertainmentcareersSpider.listing_url_pattern
HINTS = EntertainmentcareersSpider.index_hint_selectors


def rebuild(response, body_text):
    return HtmlResponse(url=response.url, body=body_text.encode("utf-8"), encoding="utf-8")


def test_recovers_when_every_css_class_is_renamed(ec_search_response):
    """A pure restyle: classes change, URLs do not. Hints miss, pattern holds."""
    drifted = rebuild(
        ec_search_response,
        re.sub(r'class="[^"]*"', 'class="totally-new-design"', ec_search_response.text),
    )

    assert not any(drifted.xpath(hint).getall() for hint in HINTS), "hints should miss"
    urls = discover_links(drifted, PATTERN, HINTS)
    assert len(urls) >= 10
    assert all("/job/" in u for u in urls)


def test_recovers_when_url_scheme_changes(ec_search_response):
    """A URL rewrite the configured pattern cannot match; inference must."""
    drifted = rebuild(
        ec_search_response,
        re.sub(
            r'href="/([\w-]+)/([\w-]+)/job/(\d+)/"',
            r'href="/positions/\3-\2"',
            ec_search_response.text,
        ),
    )

    assert discover_links(drifted, PATTERN, HINTS) == [], "old pattern must now miss"

    candidates = infer_listing_patterns(drifted)
    assert candidates, "inference found no repeated link family"

    recovered = set()
    for pattern, _count, _example in candidates[:3]:
        recovered |= set(discover_links(drifted, pattern))
    assert len(recovered) >= 10
    assert all("/positions/" in u for u in recovered)


def test_recovers_when_classes_and_urls_both_change(ec_search_response):
    """Full redesign. Only the link-shape signal survives, and it is enough."""
    text = re.sub(r'class="[^"]*"', 'class="x"', ec_search_response.text)
    text = re.sub(r'href="/([\w-]+)/([\w-]+)/job/(\d+)/"', r'href="/roles/\3/\2"', text)
    drifted = rebuild(ec_search_response, text)

    assert discover_links(drifted, PATTERN, HINTS) == []

    candidates = infer_listing_patterns(drifted)
    recovered = set()
    for pattern, _count, _example in candidates[:3]:
        recovered |= set(discover_links(drifted, pattern))
    assert len(recovered) >= 10
    assert all("/roles/" in u for u in recovered)


def test_inference_ignores_navigation_and_boilerplate(ec_search_response):
    """Recovery must not "succeed" by latching onto nav links."""
    for pattern, _count, example in infer_listing_patterns(ec_search_response)[:3]:
        assert not re.search(r"/(about|privacy|terms|login|contact)", example)


def test_spider_reports_inferred_pattern_and_uses_it(ec_search_response):
    """End to end: the spider itself recovers and yields follow requests."""

    class Drifted(ResilientListingSpider):
        name = "drifted"
        listing_url_pattern = r"/this/never/matches/\d+$"

    spider = Drifted()
    text = re.sub(
        r'href="/([\w-]+)/([\w-]+)/job/(\d+)/"', r'href="/openings/\3"', ec_search_response.text
    )
    requests = list(spider.parse(rebuild(ec_search_response, text)))

    followed = [r.url for r in requests if "/openings/" in r.url]
    assert len(followed) >= 10
    assert spider.diag["discovery_inferred"] == 1
    assert spider.diag["listings_discovered"] >= 10


def test_feed_fallback_reads_entries_when_page_has_no_links():
    """With no usable links, an advertised feed still yields listings."""
    page = HtmlResponse(
        url="https://example.com/jobs",
        body=b'<html><head><link rel="alternate" type="application/rss+xml"'
        b' href="/jobs/feed.xml"></head><body><p>rendered by javascript</p></body></html>',
        encoding="utf-8",
    )
    assert feed_urls(page) == ["https://example.com/jobs/feed.xml"]

    feed = XmlResponse(
        url="https://example.com/jobs/feed.xml",
        body=b"""<?xml version="1.0"?><rss version="2.0"><channel>
        <item><link>https://example.com/jobs/1</link></item>
        <item><link>https://example.com/jobs/2</link></item>
        </channel></rss>""",
        encoding="utf-8",
    )
    assert feed_entry_links(feed) == [
        "https://example.com/jobs/1",
        "https://example.com/jobs/2",
    ]
