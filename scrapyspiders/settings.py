BOT_NAME = "scrapyspiders"

SPIDER_MODULES = ["scrapyspiders.spiders"]
NEWSPIDER_MODULE = "scrapyspiders.spiders"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 1.5
COOKIES_ENABLED = False

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 30.0

RETRY_ENABLED = True
RETRY_TIMES = 2

ITEM_PIPELINES = {
    "scrapyspiders.pipelines.EmailDedupePipeline": 300,
}

# To resume an interrupted crawl: scrapy crawl <name> -s JOBDIR=.jobdirs/<name>
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
