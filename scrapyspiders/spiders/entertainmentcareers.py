import re

import scrapy

from scrapyspiders.items import EmailLeadItem
from scrapyspiders.keywords import KEYWORDS


class EntertainmentcareersSpider(scrapy.Spider):
    name = "entertainmentcareers"
    allowed_domains = ["entertainmentcareers.net"]

    # TODO: selectors are unverified against current entertainmentcareers.net
    # markup; this spider never ran previously (the old source had a
    # syntax error and could not be imported).
    def start_requests(self):
        for key in KEYWORDS:
            query = re.sub(" ", "+", key)
            yield scrapy.Request(
                url=f"https://www.entertainmentcareers.net/psearch/?zoom_query={query}",
                callback=self.parse,
            )

    def parse(self, response):
        links = response.xpath('//*[@class="results_title"]/a/@href').getall()
        for link in links:
            yield response.follow(link, callback=self.parse_page)

    def parse_page(self, response):
        match = re.search(r"(\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6})", response.text)
        if match:
            yield EmailLeadItem(email=match.group(1), source_url=response.url, spider=self.name)
