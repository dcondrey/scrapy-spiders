"""Shared spider behaviour: durable extraction plus drift diagnostics.

Two entry shapes are supported. ResilientListingSpider walks an HTML index and
finds listings by URL shape; a SitemapSpider subclass gets its URLs from the
site's own sitemap. Both share ListingExtractionMixin, so a listing is parsed
the same way regardless of how it was found.

The ordering principle throughout: read machine-readable metadata first
(schema.org JSON-LD, <time datetime>, sitemap <lastmod>), because sites
maintain those for aggregators and they survive visual redesigns. Reach for
CSS classes only when nothing structured is present.
"""

from collections import Counter
from datetime import date, timedelta

import scrapy

from scrapyspiders.discovery import (
    feed_entry_links,
    feed_urls,
    infer_listing_patterns,
)
from scrapyspiders.extract import (
    discover_links,
    extract_listing_fields,
    extract_posted_date,
    find_emails,
)
from scrapyspiders.items import JobLeadItem


class ListingExtractionMixin:
    """Parse one listing detail page and record which strategies worked."""

    default_max_age_days = 7
    require_date = False
    require_email = False

    def init_diagnostics(self, days=None):
        self.max_age_days = int(days) if days is not None else self.default_max_age_days
        self.today = date.today()
        self.diag = Counter()
        self.date_strategies = Counter()

    def parse_listing(self, response):
        self.diag["listings_fetched"] += 1
        posted, strategy = extract_posted_date(response, today=self.today)
        self.date_strategies[strategy] += 1

        if posted is None:
            self.diag["undated"] += 1
            if self.require_date:
                return
        elif not self.within_window(posted):
            self.diag["outside_window"] += 1
            return

        fields = extract_listing_fields(response)
        if not fields["title"]:
            self.diag["no_title"] += 1

        emails = self.emails_for(response)
        if emails:
            self.diag["listings_with_email"] += 1
        elif self.require_email:
            self.diag["dropped_no_email"] += 1
            return

        self.diag["items_yielded"] += 1
        yield JobLeadItem(
            title=fields["title"],
            company=fields["company"],
            location=fields["location"],
            posted_date=posted.isoformat() if posted else None,
            date_source=strategy,
            source_url=response.url,
            spider=self.name,
            email=emails[0] if emails else None,
        )

    def emails_for(self, response):
        """Page-wide scan, plus mailto: hrefs the regex would not reach."""
        found = find_emails(response.text)
        for href in response.xpath("//a/@href").getall():
            if href and href.lower().startswith("mailto:"):
                address = href.split(":", 1)[1].split("?")[0].strip()
                if address and address not in found:
                    found.append(address)
        return [e for e in found if not self.is_boilerplate_email(e)]

    def is_boilerplate_email(self, email):
        return email.lower() in getattr(self, "ignored_emails", frozenset())

    def within_window(self, posted):
        if self.max_age_days is None:
            return True
        return timedelta(0) <= (self.today - posted) <= timedelta(days=self.max_age_days)

    def report_diagnostics(self):
        self.logger.info(
            "%s diagnostics: %s | date strategies: %s",
            self.name,
            dict(self.diag),
            dict(self.date_strategies),
        )
        if self.diag["listings_fetched"] and not self.diag["items_yielded"]:
            self.logger.error(
                "%s fetched %d listing page(s) but yielded nothing (undated: %d, "
                "outside window: %d). Widen the window with -a days=N before "
                "assuming the selectors broke.",
                self.name,
                self.diag["listings_fetched"],
                self.diag["undated"],
                self.diag["outside_window"],
            )


class ResilientListingSpider(ListingExtractionMixin, scrapy.Spider):
    """Find listings on an HTML index by URL shape, not DOM position.

    Discovery cascades: the configured pattern, then a pattern inferred from
    the page's own link structure, then any RSS/Atom feed the page advertises.
    A site can rename every CSS class, or change its URL scheme outright, and
    the inference step still finds the listing family.
    """

    listing_url_pattern = None
    index_hint_selectors = ()
    pagination_selectors = (
        '//a[@rel="next"]/@href',
        '//link[@rel="next"]/@href',
        '//a[contains(translate(text(),"NEXT","next"),"next")]/@href',
    )
    follow_pagination = True
    max_index_pages = 5

    def __init__(self, days=None, max_pages=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.listing_url_pattern is None:
            raise ValueError(f"{type(self).__name__} must set listing_url_pattern")
        self.init_diagnostics(days)
        if max_pages is not None:
            self.max_index_pages = int(max_pages)
        self.seen_listings = set()

    def parse(self, response):
        self.diag["index_pages"] += 1
        urls = discover_links(response, self.listing_url_pattern, self.index_hint_selectors)
        if urls:
            self.diag["discovery_configured"] += 1
        else:
            urls = self.recover_by_inference(response)

        new_urls = [u for u in urls if u not in self.seen_listings]
        self.seen_listings.update(new_urls)
        self.diag["listings_discovered"] += len(new_urls)

        for url in new_urls:
            yield response.follow(url, callback=self.parse_listing)

        if not urls:
            yield from self.recover_by_feed(response)

        if self.follow_pagination and self.diag["index_pages"] < self.max_index_pages:
            yield from self.follow_next_page(response)

    def recover_by_inference(self, response):
        """Learn the listing URL family from the page when the pattern misses."""
        candidates = infer_listing_patterns(response)
        if not candidates:
            return []
        pattern, count, example = candidates[0]
        self.logger.warning(
            "%s: configured pattern %r matched nothing on %s. Inferred %r "
            "from %d similar links (e.g. %s). Update listing_url_pattern.",
            self.name,
            self.listing_url_pattern,
            response.url,
            pattern,
            count,
            example,
        )
        self.diag["discovery_inferred"] += 1
        return discover_links(response, pattern)

    def recover_by_feed(self, response):
        """Last resort: an RSS/Atom feed, whose format never drifts."""
        for url in feed_urls(response):
            self.diag["discovery_feed_probed"] += 1
            self.logger.warning("%s: falling back to feed %s", self.name, url)
            yield response.follow(url, callback=self.parse_feed)

    def parse_feed(self, response):
        links = feed_entry_links(response)
        self.diag["feed_entries"] += len(links)
        for url in links:
            if url not in self.seen_listings:
                self.seen_listings.add(url)
                yield response.follow(url, callback=self.parse_listing)

    def follow_next_page(self, response):
        for selector in self.pagination_selectors:
            href = response.xpath(selector).get()
            if href:
                self.diag["pagination_followed"] += 1
                yield response.follow(href, callback=self.parse)
                return

    def closed(self, reason):
        self.report_diagnostics()
        if self.diag["index_pages"] and not self.diag["listings_discovered"]:
            self.logger.error(
                "%s discovered 0 listings across %d index page(s). Pattern %r "
                "matched nothing, inference found no repeated link family, and "
                "no feed was advertised. The site likely renders results with "
                "JavaScript; this spider needs a browser engine or a data feed.",
                self.name,
                self.diag["index_pages"],
                self.listing_url_pattern,
            )
