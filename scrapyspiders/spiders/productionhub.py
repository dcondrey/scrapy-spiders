from urllib.parse import quote_plus

import scrapy

from scrapyspiders.base import ResilientListingSpider
from scrapyspiders.keywords import KEYWORDS


class ProductionhubSpider(ResilientListingSpider):
    """ProductionHub job board.

    STATUS as of 2026-09-11: productionhub.com serves a Cloudflare JS
    challenge ("Just a moment...") and returns HTTP 403 to plain HTTP
    clients, so this spider yields nothing until it is run through a browser
    engine.
    """

    name = "productionhub"
    allowed_domains = ["productionhub.com"]
    listing_url_pattern = r"/jobs?/[\w-]+/?$|/jobs?/\d+"
    ignored_emails = frozenset({"press@productionhub.com"})

    async def start(self):
        for keyword in KEYWORDS:
            yield scrapy.Request(
                url=f"https://www.productionhub.com/jobs/search?q={quote_plus(keyword)}",
                callback=self.parse,
            )
