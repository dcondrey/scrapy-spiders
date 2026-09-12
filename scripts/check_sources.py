"""Report whether each spider's source site is still reachable and scrapable.

Run by the weekly CI job. These spiders break because sites redesign, move,
or start challenging bots, and none of that shows up in a unit test. Exits
non-zero if every source is unusable.
"""

import contextlib
import sys
import urllib.error
import urllib.request

from scrapyspiders.middlewares import CHALLENGE_SIGNATURES

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

SOURCES = {
    "entertainmentcareers": "https://www.entertainmentcareers.net/psearch/?zoom_query=film+editor",
    "craiglist": "https://www.craigslist.org/sitemap-index-postings-00.xml",
    "mandy": "https://www.mandy.com/jobs?q=film+editor",
    "productionhub": "https://www.productionhub.com/jobs",
    "newenglandfilm": "https://wifvnejobs.org/",
}


def probe(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(20000).decode("utf-8", "ignore")
            return response.status, classify(body)
    except urllib.error.HTTPError as exc:
        body = ""
        with contextlib.suppress(OSError):
            body = exc.read(20000).decode("utf-8", "ignore")
        return exc.code, classify(body)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, f"unreachable: {exc}"


def classify(body):
    for vendor, pattern in CHALLENGE_SIGNATURES:
        if pattern.search(body):
            return f"{vendor} challenge"
    return "ok"


def main():
    usable = 0
    for name, url in sorted(SOURCES.items()):
        status, note = probe(url)
        healthy = status == 200 and note == "ok"
        usable += healthy
        line = f"{'PASS' if healthy else 'FAIL'}  {name:22} {status}  {note}  {url}"
        sys.stdout.write(line + "\n")

    sys.stdout.write(f"\n{usable}/{len(SOURCES)} sources usable\n")
    return 0 if usable else 1


if __name__ == "__main__":
    sys.exit(main())
