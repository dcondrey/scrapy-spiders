from scrapyspiders.base import ResilientListingSpider


class NewenglandfilmSpider(ResilientListingSpider):
    """NewEnglandFilm.com job listings.

    STATUS as of 2026-09-11: the original https://newenglandfilm.com/jobs.htm
    returns 404. The site's jobs link now points at wifvnejobs.org, whose
    public pages carry no listings (they appear to be behind membership), so
    there is currently no anonymous listing index to crawl. The start URL
    below follows the current link; the spider reports zero discoveries
    rather than failing silently.
    """

    name = "newenglandfilm"
    allowed_domains = ["newenglandfilm.com", "wifvnejobs.org"]
    start_urls = ["https://wifvnejobs.org/"]
    listing_url_pattern = r"/jobs?/[\w-]+|/[\w-]+/job/\d+"
