from pathlib import Path

from scrapy.exceptions import DropItem


class EmailDedupePipeline:
    """Append newly seen emails to <spider name>.txt; drop repeats."""

    def open_spider(self, spider):
        self.path = Path(f"{spider.name}.txt")
        if self.path.exists():
            self.seen = set(self.path.read_text(encoding="utf-8").splitlines())
        else:
            self.seen = set()
        self.handle = self.path.open("a", encoding="utf-8")

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
