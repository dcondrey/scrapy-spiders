import scrapy


class EmailLeadItem(scrapy.Item):
    email = scrapy.Field()
    source_url = scrapy.Field()
    spider = scrapy.Field()
