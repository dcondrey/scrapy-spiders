from scrapyspiders.base import ResilientListingSpider

# robots.txt disallows /jobs/search*, so the keyword search endpoint is off
# limits to a crawler. The category indexes are allowed and better targeted.
CATEGORY_PATHS = (
    "film-movie",
    "television",
    "commercial",
    "documentary",
    "corporate-video",
    "music-video",
)


class ProductionhubSpider(ResilientListingSpider):
    """ProductionHub job board, crawled through its category indexes.

    Two constraints shape this spider. robots.txt disallows /jobs/search*,
    so keyword search is unavailable to a crawler; and Cloudflare rejects
    ordinary HTTP clients with 403, so pages are only reachable when
    IMPERSONATE is enabled. See the README before enabling that.

    Detail pages publish schema.org JobPosting, so dates and fields come
    from structured data.
    """

    name = "productionhub"
    allowed_domains = ["productionhub.com"]

    # Verified 2026-09-11: /job/<id>/<title-slug>
    listing_url_pattern = r"/job/\d+/[\w-]+/?$"
    start_urls = [f"https://www.productionhub.com/jobs/type/{p}" for p in CATEGORY_PATHS]
    ignored_emails = frozenset({"press@productionhub.com"})
