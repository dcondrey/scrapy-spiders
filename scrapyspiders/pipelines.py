from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class SeenUrlDedupePipeline:
    """Drop listings already recorded by a previous run.

    Keyed on source_url rather than email, because most listings now carry no
    email at all and would otherwise collapse into a single None.

    Uses from_crawler and takes no spider argument: Scrapy 2.19 deprecates
    passing the spider into pipeline methods.
    """

    def __init__(self, crawler, path):
        self.crawler = crawler
        self.path = path
        self.handle = None
        self.seen = set()
        self.dropped = 0

    @classmethod
    def from_crawler(cls, crawler):
        configured = crawler.settings.get("SEEN_URLS_FILE")
        return cls(crawler, Path(configured) if configured else None)

    def open_spider(self):
        if self.path is None:
            self.path = Path(f"seen-{self.crawler.spider.name}.txt")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.seen = set(self.path.read_text(encoding="utf-8").split())
        self.handle = self.path.open("a", encoding="utf-8")

    def close_spider(self):
        if self.handle is not None:
            self.handle.close()
        if self.dropped:
            self.crawler.spider.logger.info(
                "Skipped %d listing(s) already seen in %s", self.dropped, self.path
            )

    def process_item(self, item):
        url = ItemAdapter(item).get("source_url")
        if not url:
            return item
        if url in self.seen:
            self.dropped += 1
            raise DropItem("already seen")
        self.seen.add(url)
        if self.handle is not None:
            self.handle.write(url + "\n")
            self.handle.flush()
        return item
