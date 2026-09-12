import scrapy


class JobLeadItem(scrapy.Item):
    """A job listing, with a contact email when the page exposes one.

    email is optional by design: most listing sites now route applications
    through a form or an external redirect rather than publishing an address.
    """

    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    posted_date = scrapy.Field()
    date_source = scrapy.Field()
    source_url = scrapy.Field()
    spider = scrapy.Field()
    email = scrapy.Field()
