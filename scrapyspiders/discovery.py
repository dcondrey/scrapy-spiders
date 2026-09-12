"""Finding listing URLs when the configured selectors stop working.

Ordered by durability. Sitemaps and feeds are contracts a site publishes for
machines and survive visual redesigns untouched; an inferred URL template
survives a CSS rewrite; a hand-written selector survives neither. The base
spider walks this list until something returns links.
"""

import re
from collections import Counter
from urllib.parse import urljoin, urlparse

_NUMERIC = re.compile(r"^\d+$")
_SLUGGY = re.compile(r"^[\w-]{3,}$")
_DATEISH = re.compile(r"^(19|20)\d{2}$")

# Paths that repeat site-wide but never identify a listing.
_BORING = re.compile(
    r"(^|/)(about|contact|privacy|terms|login|signin|signup|register|account|"
    r"cart|search|category|categories|tag|tags|page|feed|rss|sitemap|help|faq|"
    r"advertise|subscribe|newsletter|css|js|img|images|static|assets)(/|$)",
    re.I,
)


def path_template(path):
    """Reduce a URL path to a shape: /jobs/12345/some-slug -> /jobs/{n}/{s}."""
    parts = []
    for segment in path.strip("/").split("/"):
        if not segment:
            continue
        if _NUMERIC.match(segment):
            parts.append("{n}" if not _DATEISH.match(segment) else "{y}")
        elif _SLUGGY.match(segment) and (
            any(ch.isdigit() for ch in segment) or "-" in segment or len(segment) > 12
        ):
            parts.append("{s}")
        else:
            parts.append(segment)
    return "/" + "/".join(parts)


def template_to_regex(template):
    """Turn a shape back into a path regex that matches its whole family."""
    out = []
    for segment in template.strip("/").split("/"):
        if segment == "{n}":
            out.append(r"\d+")
        elif segment == "{y}":
            out.append(r"(?:19|20)\d{2}")
        elif segment == "{s}":
            out.append(r"[\w-]+")
        elif segment:
            out.append(re.escape(segment))
    return "^/" + "/".join(out) + "/?$"


def infer_listing_patterns(response, min_count=3, same_host_only=True):
    """Learn candidate listing-URL patterns from the links on a page.

    A listing index is by construction a page full of links that share a shape
    and differ only in an id or slug. Counting shapes finds that family without
    knowing anything about the site's markup.

    Returns [(path_regex, count, example_url)], most frequent first.
    """
    host = urlparse(response.url).netloc
    shapes = Counter()
    examples = {}

    for href in response.xpath("//a/@href").getall():
        if not href or href.startswith(("mailto:", "javascript:", "#", "tel:")):
            continue
        absolute = urljoin(response.url, href.strip())
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if same_host_only and parsed.netloc != host:
            continue
        path = parsed.path
        if not path or path == "/" or _BORING.search(path):
            continue
        # A listing URL is a leaf, not a section index.
        if path.strip("/").count("/") < 1:
            continue
        shape = path_template(path)
        # Require a variable segment; a fixed path repeated is navigation.
        if "{n}" not in shape and "{s}" not in shape:
            continue
        shapes[shape] += 1
        examples.setdefault(shape, absolute)

    return [
        (template_to_regex(shape), count, examples[shape])
        for shape, count in shapes.most_common()
        if count >= min_count
    ]


def feed_urls(response):
    """RSS/Atom feed URLs advertised by the page."""
    urls = []
    for href in response.xpath(
        '//link[contains(@type,"rss") or contains(@type,"atom")]/@href'
    ).getall():
        absolute = urljoin(response.url, href.strip())
        if absolute not in urls:
            urls.append(absolute)
    return urls


def sitemap_links(response):
    """URLs from a sitemap or sitemap index, namespace-agnostic."""
    urls = response.xpath("//*[local-name()='loc']/text()").getall()
    return [u.strip() for u in urls if u and u.strip()]


def feed_entry_links(response):
    """Item/entry links from an RSS or Atom document."""
    urls = response.xpath("//*[local-name()='item']/*[local-name()='link']/text()").getall()
    if not urls:
        urls = response.xpath("//*[local-name()='entry']/*[local-name()='link']/@href").getall()
    return [u.strip() for u in urls if u and u.strip()]
