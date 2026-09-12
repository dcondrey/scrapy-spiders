from urllib.parse import quote_plus

import scrapy

from scrapyspiders.base import ResilientListingSpider
from scrapyspiders.keywords import KEYWORDS


class MandySpider(ResilientListingSpider):
    """Mandy.com crew and production jobs.

    STATUS as of 2026-09-11: mandy.com sits behind a Cloudflare managed
    challenge and returns HTTP 403 to every plain HTTP client, so this spider
    yields nothing until it is run through a browser engine. The middleware
    reports the challenge explicitly rather than letting the run look empty.
    """

    name = "mandy"
    allowed_domains = ["mandy.com"]
    listing_url_pattern = r"/job/[\w-]+|/jobs?/\d+"

    async def start(self):
        for keyword in KEYWORDS:
            yield scrapy.Request(
                url=f"https://www.mandy.com/jobs?q={quote_plus(keyword)}",
                callback=self.parse,
            )
