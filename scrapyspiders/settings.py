BOT_NAME = "scrapyspiders"

SPIDER_MODULES = ["scrapyspiders.spiders"]
NEWSPIDER_MODULE = "scrapyspiders.spiders"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Craigslist disallows /reply (the contact relay) but permits /view and the
# sitemaps this project actually reads, so obeying robots costs nothing here.
ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 1.0
DOWNLOAD_TIMEOUT = 30
COOKIES_ENABLED = False

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 30.0

RETRY_ENABLED = True
RETRY_TIMES = 2

# A keyword crawl fans out fast; keep an unattended run bounded.
CLOSESPIDER_TIMEOUT = 1800
CLOSESPIDER_ITEMCOUNT = 2000

HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = ".httpcache"

DOWNLOADER_MIDDLEWARES = {
    "scrapyspiders.middlewares.BotChallengeDetectionMiddleware": 560,
}

ITEM_PIPELINES = {
    "scrapyspiders.pipelines.SeenUrlDedupePipeline": 300,
}

# Where the cross-run "already collected" list lives. None means one file per
# spider in the working directory.
SEEN_URLS_FILE = None

# To resume an interrupted crawl: scrapy crawl <name> -s JOBDIR=.jobdirs/<name>
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
