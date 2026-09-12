import re
from datetime import date, timedelta

from scrapy.spiders import SitemapSpider

from scrapyspiders.base import ListingExtractionMixin
from scrapyspiders.keywords import KEYWORDS

# Craigslist's own posting sitemaps, one per city and category per day.
SITEMAP_INDEXES = [
    f"https://www.craigslist.org/sitemap-index-postings-{n:02d}.xml" for n in range(0, 4)
]

# jjj = jobs, ggg = gigs. Both carry paid work.
CATEGORY_CODES = ("jjj", "ggg")


class CraiglistSpider(ListingExtractionMixin, SitemapSpider):
    """Craigslist postings, enumerated from the public sitemaps.

    Craigslist's search UI renders results with JavaScript and returns an
    empty shell to an HTTP client, so the search path cannot work without a
    browser engine. The sitemaps are XML, published for crawlers, carry
    <lastmod> dates, and are the durable way in.

    Postings do not expose an email: Craigslist proxies contact through
    /reply, which its robots.txt disallows. This spider therefore collects
    listings, and email stays None.
    """

    name = "craiglist"
    allowed_domains = ["craigslist.org"]
    sitemap_urls = SITEMAP_INDEXES
    sitemap_rules = [(r"/view/d/", "parse_listing"), (r"/d/[\w-]+/\w+\.html", "parse_listing")]

    custom_settings = {
        # Sitemap enumeration reaches far more URLs than a keyword search, so
        # bound the run rather than walking every city.
        "CLOSESPIDER_ITEMCOUNT": 500,
        "CLOSESPIDER_TIMEOUT": 900,
    }

    def __init__(self, days=None, cities=None, categories=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_diagnostics(days)
        self.cities = {c.strip().lower() for c in cities.split(",")} if cities else None
        self.categories = (
            tuple(c.strip().lower() for c in categories.split(","))
            if categories
            else CATEGORY_CODES
        )
        # Word boundaries matter: without them "editor" matches "Expeditor"
        # and the crawl fills up with restaurant jobs.
        self.keyword_re = re.compile(
            r"\b(?:" + "|".join(re.escape(k) for k in KEYWORDS) + r")\b",
            re.IGNORECASE,
        )

    def sitemap_filter(self, entries):
        """Narrow the crawl twice before a single posting is downloaded.

        First to recent sitemaps for the requested cities and categories, then
        to postings whose URL slug mentions a keyword. Craigslist puts the
        listing title in the path, so this pre-filter is free and removes the
        overwhelming majority of fetches: the sitemaps cover every job in a
        city, of which film work is a small fraction.
        """
        cutoff = date.today() - timedelta(days=self.max_age_days or 7)
        for entry in entries:
            loc = entry.get("loc", "")
            if loc.endswith(".xml"):
                if not self.wanted_sitemap(loc, cutoff):
                    continue
                self.diag["sitemaps_kept"] += 1
            else:
                if not self.keyword_re.search(self.slug_of(loc)):
                    self.diag["slug_prefilter_skipped"] += 1
                    continue
                self.diag["slug_prefilter_kept"] += 1
            yield entry

    @staticmethod
    def slug_of(url):
        """The human-readable title slug craigslist embeds in a posting URL."""
        return url.rstrip("/").rsplit("/", 2)[-2].replace("-", " ") if "/" in url else ""

    def wanted_sitemap(self, loc, cutoff):
        if not any(loc.endswith(f"-{code}.xml") for code in self.categories):
            return False
        if self.cities and not any(f"-{city}-" in loc for city in self.cities):
            return False
        found = re.search(r"(\d{4}-\d{2}-\d{2})", loc)
        if found:
            try:
                if date.fromisoformat(found.group(1)) < cutoff:
                    return False
            except ValueError:
                pass
        return True

    def parse_listing(self, response):
        """Keyword-filter before emitting; the sitemap is not searchable."""
        haystack = " ".join(
            filter(
                None,
                [
                    response.xpath("//title/text()").get(),
                    response.xpath('//*[@id="titletextonly"]//text()').get(),
                    response.xpath('//section[@id="postingbody"]//text()').get(),
                ],
            )
        )
        if haystack and not self.keyword_re.search(haystack):
            self.diag["keyword_miss"] += 1
            return
        for item in super().parse_listing(response):
            # <title> carries " - <category> - craigslist" boilerplate; the
            # posting's own heading does not.
            heading = response.xpath('//*[@id="titletextonly"]//text()').get()
            if heading:
                item["title"] = " ".join(heading.split())
            yield item

    def closed(self, reason):
        self.report_diagnostics()
