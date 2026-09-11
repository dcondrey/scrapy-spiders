from datetime import datetime

import scrapy

from scrapyspiders.items import EmailLeadItem


class NewenglandfilmSpider(scrapy.Spider):
    name = "newenglandfilm"
    allowed_domains = ["newenglandfilm.com"]
    start_urls = ["https://newenglandfilm.com/jobs.htm"]

    # TODO: fixed div[1..30] indexing is unverified against current markup
    # and raises IndexError if the listing page has fewer entries.
    def parse(self, response):
        current_date = datetime.today().strftime("%m/%d/%Y")
        for num_div in range(1, 31):
            dates = response.xpath(f'//*[@id="mainContent"]/div[{num_div}]/span/text()').re(
                r"(\d{1,2}/\d{1,2}/\d{4})"
            )
            if not dates:
                continue
            emails = response.xpath(f'//*[@id="mainContent"]/div[{num_div}]/div/text()').re(
                r"(\w+@[a-zA-Z0-9_]+?\.[a-zA-Z]{2,6})"
            )
            if dates[0] == current_date:
                for address in emails:
                    yield EmailLeadItem(email=address, source_url=response.url, spider=self.name)
