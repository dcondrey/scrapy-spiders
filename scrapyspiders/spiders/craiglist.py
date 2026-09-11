import re
from datetime import datetime

import scrapy

from scrapyspiders.items import EmailLeadItem
from scrapyspiders.keywords import KEYWORDS


class CraiglistSpider(scrapy.Spider):
    name = "craiglist"
    allowed_domains = ["craigslist.org"]
    start_urls = ["https://www.craigslist.org/about/sites"]

    # TODO: positional-index XPaths below (div[N]/p[N]) are unverified
    # against current craigslist markup; treat as a starting point.
    # TODO: listing dates carry no year, so current_date matching is
    # ambiguous across a year boundary; harmless day-to-day, wrong for
    # exactly one day each December 31 / January 1.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = [re.sub(" ", "+", k) for k in KEYWORDS]
        self.current_date = datetime.today().strftime("%b %d")

    def parse(self, response):
        links = response.xpath('//*[@id="pagecontainer"]/section/div/div/ul/li/a/@href').getall()
        for link in links:
            for key in self.keywords:
                yield scrapy.Request(
                    url=(
                        f"{link}/search/ggg?zoomToPosting=&catAbb=ggg&query={key}"
                        "&minAsk=&maxAsk=&sort=rel&excats="
                    ),
                    callback=self.parse_catalog,
                )

    def parse_catalog(self, response):
        count = response.xpath('//*[@id="toc_rows"]/div[1]/div/span[2]/span[3]/span/text()').getall()
        if not count:
            return
        total = int(count[0])
        if total <= 100:
            for i in range(1, total + 1):
                link = response.xpath(f'//*[@id="toc_rows"]/div[2]/p[{i}]/span[2]/a/@href').get()
                date = response.xpath(f'//*[@id="toc_rows"]/div[2]/p[{i}]/span[2]/span/text()').get()
                if not link or not date:
                    continue
                try:
                    if self.current_date == datetime.strptime(date, "%b %d").strftime("%b %d"):
                        num = link.split("/")[-1].split(".")[0]
                        site = link.split("/")[2]
                        yield scrapy.Request(
                            url=f"https://{site}/reply/{num}", callback=self.parse_page
                        )
                except (ValueError, UnicodeEncodeError):
                    site = response.url.split("/")[2]
                    yield scrapy.Request(url=f"https://{site}{link}", callback=self.parse_bad_date)
        else:
            for count_page in range(0, total, 100):
                if count_page == 0:
                    yield scrapy.Request(url=response.url, callback=self.parse_links)
                else:
                    key = response.xpath('//*[@id="query"]/@value').get()
                    site = response.url.split("/")[2]
                    yield scrapy.Request(
                        url=f"https://{site}/search/ggg?s={count_page}&catAbb=ggg&query={key}&sort=rel",
                        callback=self.parse_links,
                    )

    def parse_links(self, response):
        counts = response.xpath('//*[@id="toc_rows"]/div[1]/div/span[2]/span[1]/text()').re(r"(\d+)")
        if len(counts) < 2:
            return
        total = int(counts[1]) - int(counts[0]) + 2
        for i in range(1, total):
            link = response.xpath(f'//*[@id="toc_rows"]/div[2]/p[{i}]/span[2]/a/@href').get()
            date = response.xpath(f'//*[@id="toc_rows"]/div[2]/p[{i}]/span[2]/span/text()').get()
            if not link or not date:
                continue
            if self.current_date == datetime.strptime(date, "%b %d").strftime("%b %d"):
                num = link.split("/")[-1].split(".")[0]
                site = response.url.split("/")[2]
                yield scrapy.Request(url=f"https://{site}/reply/{num}", callback=self.parse_page)

    def parse_bad_date(self, response):
        date = response.xpath(
            '//*[@id="pagecontainer"]/section/section[2]/div[2]/p[3]/time/text()'
        ).re(r"(\d{4}-\d{1,2}-\d{1,2})")
        if not date:
            date = response.xpath(
                '//*[@id="pagecontainer"]/section/section[2]/div[2]/p[2]/time/text()'
            ).re(r"(\d{4}-\d{1,2}-\d{1,2})")
        if date and self.current_date == datetime.strptime(date[0], "%Y-%m-%d").strftime("%b %d"):
            yield response.follow(response.url, callback=self.parse_page, dont_filter=True)

    def parse_page(self, response):
        email = response.xpath("//div/ul//input/@value").get()
        if email:
            yield EmailLeadItem(email=email, source_url=response.url, spider=self.name)
