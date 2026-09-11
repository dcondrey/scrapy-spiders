import re
from datetime import datetime

import scrapy

from scrapyspiders.emailmatch import find_first_email
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
        email = find_first_email(response.text)
        if email:
            yield EmailLeadItem(email=email, source_url=response.url, spider=self.name)
