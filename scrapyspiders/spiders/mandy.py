import re
from datetime import datetime

import scrapy

from scrapyspiders.items import EmailLeadItem
from scrapyspiders.keywords import KEYWORDS


class MandySpider(scrapy.Spider):
    name = "mandy"
    allowed_domains = ["mandy.com"]

    def start_requests(self):
        current_date = datetime.today().strftime("%d-%b-%Y")
        self.current_date = current_date
        for key in KEYWORDS:
            query = re.sub(" ", "+", key)
            yield scrapy.Request(
                url=f"https://mandy.com/1/search.cfm?fs=1&place=wld&city=&what={query}&where=Worldwide",
                callback=self.parse,
            )

    def parse(self, response):
        dates = response.xpath(
            '//*[@id="resultswrapper"]/section/div/div/div/div/span/text()'
        ).getall()
        links = response.xpath(
            '//*[@id="resultswrapper"]/section/div/div/div/div/a/@href'
        ).getall()
        parsed_dates = []
        for raw in dates:
            match = re.findall(r"\w+:\D([A-Za-z0-9-]+)", raw)
            parsed_dates.append(match[0] if match else None)
        for link, date in zip(links, parsed_dates):
            if date == self.current_date:
                yield response.follow(link, callback=self.parse_page)

    def parse_page(self, response):
        email = response.text
        match = re.search(r"(\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6})", email)
        if match:
            yield EmailLeadItem(email=match.group(1), source_url=response.url, spider=self.name)
