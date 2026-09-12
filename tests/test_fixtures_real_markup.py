"""Tests against unmodified pages captured from the live sites.

These assert the site's real structure, so they fail when a site redesigns.
That failure is the point: it is the signal to update the spider. See
fixtures/PROVENANCE.md for capture URLs and dates.
"""

from datetime import date

from scrapyspiders.discovery import infer_listing_patterns, sitemap_links
from scrapyspiders.extract import (
    discover_links,
    extract_listing_fields,
    extract_posted_date,
)
from scrapyspiders.spiders.entertainmentcareers import EntertainmentcareersSpider

EC_PATTERN = EntertainmentcareersSpider.listing_url_pattern
EC_HINTS = EntertainmentcareersSpider.index_hint_selectors


def test_ec_search_page_yields_listing_urls(ec_search_response):
    urls = discover_links(ec_search_response, EC_PATTERN, EC_HINTS)
    assert len(urls) >= 10
    assert all("/job/" in u for u in urls)


def test_ec_configured_pattern_and_inference_agree(ec_search_response):
    """Inference should rediscover the same URL family the pattern encodes.

    This is what makes the recovery path trustworthy: if the hand-written
    pattern were ever deleted, inference finds the same listings.
    """
    configured = set(discover_links(ec_search_response, EC_PATTERN, EC_HINTS))
    inferred_patterns = infer_listing_patterns(ec_search_response)
    assert inferred_patterns, "no repeated link family found on a search page"

    recovered = set()
    for pattern, _count, _example in inferred_patterns[:3]:
        recovered |= set(discover_links(ec_search_response, pattern))
    assert configured & recovered


def test_ec_detail_exposes_jobposting_fields(ec_detail_response):
    fields = extract_listing_fields(ec_detail_response)
    assert fields["title"]
    assert fields["company"]


def test_ec_detail_date_comes_from_structured_data(ec_detail_response):
    posted, strategy = extract_posted_date(ec_detail_response)
    assert strategy == "jsonld-jobposting"
    assert isinstance(posted, date)


def test_craigslist_detail_date_comes_from_time_element(craigslist_detail_response):
    posted, strategy = extract_posted_date(craigslist_detail_response)
    assert posted == date(2026, 9, 11)
    assert strategy in {"time-attr", "meta", "jsonld", "jsonld-jobposting"}


def test_craigslist_sitemap_lists_posting_urls(craigslist_sitemap_response):
    urls = sitemap_links(craigslist_sitemap_response)
    assert len(urls) > 10
    assert any("craigslist.org" in u for u in urls)


def test_malformed_jsonld_still_yields_date_and_title(productionhub_detail_response):
    """ProductionHub's JobPosting block has unescaped quotes in description.

    No JSON parser accepts it, so the raw-scan fallback is the only thing
    standing between a valid posting and a silently undated item.
    """
    from scrapyspiders.extract import iter_jsonld

    types = [n.get("@type") for n in iter_jsonld(productionhub_detail_response)]
    assert "JobPosting" not in types, "fixture should still be unparseable JSON"

    posted, strategy = extract_posted_date(productionhub_detail_response)
    assert posted == date(2026, 8, 12)
    assert strategy == "jsonld-raw"

    fields = extract_listing_fields(productionhub_detail_response)
    assert fields["title"] == "Producer's Assistant"
