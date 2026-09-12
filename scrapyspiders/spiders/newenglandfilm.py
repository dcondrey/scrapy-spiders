import json
from datetime import date, timedelta

import scrapy

from scrapyspiders.extract import find_emails, parse_date_text
from scrapyspiders.items import JobLeadItem

# newenglandfilm.com retired its own board; its jobs link now points here.
# The site is WordPress, and its REST API serves the listings as JSON, which
# is more stable than any HTML the theme happens to render today.
API = "https://wifvnejobs.org/wp-json/wp/v2/posts"


class NewenglandfilmSpider(scrapy.Spider):
    """WIFVNE job board (the successor to newenglandfilm.com/jobs.htm).

    Verified 2026-09-11: newenglandfilm.com/jobs.htm is 404 and the site
    links out to wifvnejobs.org. That site's WP REST endpoint returns the
    postings directly, so there is no markup to drift.

    Volume is low and postings can be months old; widen with -a days=N.
    """

    name = "newenglandfilm"
    allowed_domains = ["wifvnejobs.org"]

    def __init__(self, days=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_age_days = int(days) if days is not None else 365
        self.today = date.today()

    async def start(self):
        yield scrapy.Request(f"{API}?per_page=50&page=1", callback=self.parse)

    def parse(self, response):
        try:
            posts = json.loads(response.text)
        except ValueError:
            self.logger.error(
                "%s: %s did not return JSON. The REST API may be disabled.",
                self.name,
                response.url,
            )
            return
        if not isinstance(posts, list):
            self.logger.error("%s: unexpected REST payload shape", self.name)
            return

        self.logger.info("%s: %d post(s) from the REST API", self.name, len(posts))
        for post in posts:
            item = self.item_for(post)
            if item is not None:
                yield item

    def item_for(self, post):
        posted = parse_date_text(post.get("date", "")[:10], today=self.today)
        if posted and (self.today - posted) > timedelta(days=self.max_age_days):
            return None
        body = post.get("content", {}).get("rendered", "")
        emails = find_emails(body)
        return JobLeadItem(
            title=self.plain(post.get("title", {}).get("rendered")),
            company=None,
            location=None,
            posted_date=posted.isoformat() if posted else None,
            date_source="wp-rest" if posted else "none",
            source_url=post.get("link"),
            spider=self.name,
            email=emails[0] if emails else None,
        )

    @staticmethod
    def plain(text):
        if not text:
            return None
        import html
        import re

        return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split()) or None
