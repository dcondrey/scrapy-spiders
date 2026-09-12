from urllib.parse import quote_plus

import scrapy

from scrapyspiders.base import ResilientListingSpider
from scrapyspiders.keywords import KEYWORDS


class EntertainmentcareersSpider(ResilientListingSpider):
    """EntertainmentCareers.net keyword search.

    Detail pages publish a schema.org JobPosting block, so title, company,
    location and date all come from structured data rather than markup.
    """

    name = "entertainmentcareers"
    allowed_domains = ["entertainmentcareers.net"]

    # Verified 2026-09-11: /<company-slug>/<title-slug>/job/<id>/
    listing_url_pattern = r"/[\w-]+/[\w-]+/job/\d+/?$"
    index_hint_selectors = (
        '//div[contains(@class,"result_title")]//a/@href',
        '//div[contains(@class,"result_block")]//a/@href',
        '//div[contains(@class,"result_altblock")]//a/@href',
    )

    async def start(self):
        for keyword in KEYWORDS:
            yield scrapy.Request(
                url=(
                    "https://www.entertainmentcareers.net/psearch/"
                    f"?zoom_query={quote_plus(keyword)}"
                ),
                callback=self.parse,
            )
