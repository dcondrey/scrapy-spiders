import re
from datetime import datetime

import scrapy

from scrapyspiders.items import EmailLeadItem
from scrapyspiders.keywords import KEYWORDS

IGNORED_EMAILS = {"press@productionhub.com"}


class ProductionhubSpider(scrapy.Spider):
    name = "productionhub"
    allowed_domains = ["productionhub.com"]

    def start_requests(self):
        self.current_date = datetime.today().strftime("%m.%d.%Y")
        for key in KEYWORDS:
            query = re.sub(" ", "%20", key)
            yield scrapy.Request(
                url=f"https://www.productionhub.com/jobs/search?q={query}",
                callback=self.parse,
            )

    def parse(self, response):
        count = response.xpath('//*[@id="main-content"]/div[3]/div/text()').re(r"\w+")
        if not count:
            return
        total = int(count[-1])
        for num_page in range(1, total + 1):
            yield response.follow(
                f"{response.url}&page={num_page}", callback=self.parse_count_page
            )

    def parse_count_page(self, response):
        links = response.xpath('//*[@id="main-content"]/div/div/div/h4/a/@href').getall()
        dates = response.xpath(
            '//*[@id="main-content"]/div[2]/div/div/div/footer/span/text()'
        ).re(r"(\d{1,2}/\d{1,2}/\d{4})")
        for link, date in zip(links, dates):
            if datetime.strptime(date, "%m/%d/%Y").strftime("%m.%d.%Y") == self.current_date:
                yield response.follow(link, callback=self.parse_page)

    def parse_page(self, response):
        emails = response.text
        for email in re.findall(r"(\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6})", emails):
            if email not in IGNORED_EMAILS:
                yield EmailLeadItem(email=email, source_url=response.url, spider=self.name)
