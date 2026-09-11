from pathlib import Path

from scrapy.exceptions import DropItem


class EmailDedupePipeline:
    """Append newly seen emails to <spider name>.txt; drop repeats."""

    def open_spider(self, spider):
        self.path = Path(f"{spider.name}.txt")
        self.seen = set(self.path.read_text().splitlines()) if self.path.exists() else set()
        self.handle = self.path.open("a")

    def close_spider(self, spider):
        self.handle.close()

    def process_item(self, item, spider):
        email = item["email"]
        if email in self.seen:
            raise DropItem(f"Duplicate email {email}")
        self.seen.add(email)
        self.handle.write(email + "\n")
        self.handle.flush()
        return item
