"""Extraction helpers that degrade gracefully when site markup changes.

Every helper here tries the most stable signal first (machine-readable
metadata) and falls back toward the most fragile (positional markup), so a
redesign costs recall rather than producing a silent zero.
"""

import json
import re
from datetime import date, datetime
from urllib.parse import urljoin, urlparse

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")

# Ordered most- to least-machine-readable. %b/%B accept both "Feb" and "February".
DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%m.%d.%Y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%b %d %Y",
    "%B %d %Y",
    "%d/%m/%Y",
)

# Same formats without a year, resolved against the current year.
YEARLESS_DATE_FORMATS = (
    "%b %d",
    "%B %d",
    "%d %b",
)

_DATE_TEXT_RE = re.compile(
    r"(\d{4}-\d{1,2}-\d{1,2}"
    r"|\d{1,2}[/.]\d{1,2}[/.]\d{2,4}"
    r"|\d{1,2}-[A-Za-z]{3,9}-\d{4}"
    r"|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}"
    r"|[A-Za-z]{3,9}\s+\d{1,2})"
)

_RELATIVE_RE = re.compile(r"(\d+)\s*(minute|hour|day|week|month)s?\s+ago", re.I)


def find_emails(text):
    """Every email-shaped string in text, in order, de-duplicated."""
    seen = []
    for match in EMAIL_RE.findall(text):
        if match not in seen:
            seen.append(match)
    return seen


def parse_date_text(text, today=None):
    """Best-effort date from a free-text fragment. Returns a date or None."""
    if not text:
        return None
    today = today or date.today()
    cleaned = " ".join(text.split())

    relative = _RELATIVE_RE.search(cleaned)
    if relative:
        amount, unit = int(relative.group(1)), relative.group(2).lower()
        days = {"minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30}[unit]
        from datetime import timedelta

        return today - timedelta(days=amount * days)

    match = _DATE_TEXT_RE.search(cleaned)
    if not match:
        return None
    candidate = match.group(1).strip().rstrip(",")

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    for fmt in YEARLESS_DATE_FORMATS:
        # Supply the year rather than letting strptime default it: parsing a
        # yearless date is deprecated in 3.13 and changes behaviour in 3.15,
        # and the 1900 default cannot represent Feb 29.
        for year in (today.year, today.year - 1):
            try:
                parsed = datetime.strptime(f"{candidate} {year}", f"{fmt} %Y").date()
            except ValueError:
                continue
            # A yearless date landing in the future belongs to last year
            # (a Dec 30 listing read on Jan 2).
            if (parsed - today).days > 1:
                continue
            return parsed
    return None


def iter_jsonld(response):
    """Every JSON-LD object embedded in the page, flattened through @graph."""
    for blob in response.xpath('//script[@type="application/ld+json"]/text()').getall():
        try:
            # strict=False tolerates literal tabs and newlines inside string
            # values. Hand-templated JSON-LD frequently contains them, and a
            # strict parse silently drops the whole JobPosting block.
            data = json.loads(blob.strip(), strict=False)
        except (ValueError, TypeError):
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                yield node
                if "@graph" in node:
                    stack.append(node["@graph"])


def jsonld_field(response, *field_names):
    """First value found under any of field_names across all JSON-LD blocks."""
    for node in iter_jsonld(response):
        for name in field_names:
            value = node.get(name)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def jsonld_raw_field(response, *field_names):
    """Pull a scalar straight out of raw JSON-LD text.

    Hand-templated JSON-LD is often invalid: unescaped quotes inside a
    description will fail any parser. The fields worth having are simple
    scalars near the top of the block, so recover them textually rather than
    discarding an otherwise perfectly good JobPosting.
    """
    blocks = response.xpath('//script[@type="application/ld+json"]/text()').getall()
    for name in field_names:
        pattern = re.compile(rf'"{re.escape(name)}"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"')
        for blob in blocks:
            match = pattern.search(blob)
            if match and match.group(1).strip():
                return match.group(1).strip()
    return None


def jsonld_node(response, type_name):
    """First JSON-LD object whose @type is type_name."""
    for node in iter_jsonld(response):
        node_type = node.get("@type")
        if node_type == type_name:
            return node
        if isinstance(node_type, list) and type_name in node_type:
            return node
    return None


def nested(node, *path):
    """Walk a dotted path through nested dicts/lists, tolerating either."""
    current = node
    for key in path:
        if isinstance(current, list):
            current = current[0] if current else None
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if isinstance(current, list):
        current = current[0] if current else None
    return current.strip() if isinstance(current, str) and current.strip() else None


def extract_listing_fields(response):
    """Title, company and location, preferring machine-readable sources.

    schema.org JobPosting first (sites maintain it for job aggregators, so it
    outlives redesigns), then OpenGraph, then visible markup.
    """
    posting = jsonld_node(response, "JobPosting") or {}

    title = (
        nested(posting, "title")
        or jsonld_raw_field(response, "title")
        or response.xpath('//meta[@property="og:title"]/@content').get()
        or response.xpath("//h1//text()").get()
        or response.xpath("//title/text()").get()
    )
    company = (
        nested(posting, "hiringOrganization", "name")
        or jsonld_raw_field(response, "hiringOrganization")
        or response.xpath('//meta[@property="og:site_name"]/@content').get()
        or first_text_by_class_hint(response, ("company", "employer", "organization"))
    )
    location = (
        nested(posting, "jobLocation", "address", "addressLocality")
        or nested(posting, "jobLocation", "name")
        or first_text_by_class_hint(response, ("location", "locale", "city"))
    )

    return {
        "title": " ".join(title.split()) if title else None,
        "company": " ".join(company.split()) if company else None,
        "location": " ".join(location.split()) if location else None,
    }


def first_text_by_class_hint(response, hints):
    """First non-empty text under an element whose class contains any hint."""
    for hint in hints:
        values = response.xpath(
            f"//*[contains(translate(@class,"
            f'"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"{hint}")]'
            f"//text()"
        ).getall()
        for value in values:
            cleaned = " ".join(value.split())
            if cleaned:
                return cleaned
    return None


def extract_posted_date(response, today=None):
    """Posting date, trying machine-readable sources before visible text.

    Returns (date_or_None, strategy_name) so callers can report which signal
    survived and alert when everything falls through to the fragile end.
    """
    posting = jsonld_node(response, "JobPosting")
    if posting:
        parsed = parse_date_text(nested(posting, "datePosted"), today=today)
        if parsed:
            return parsed, "jsonld-jobposting"

    value = jsonld_field(response, "datePosted", "datePublished", "dateCreated")
    if value:
        parsed = parse_date_text(value, today=today)
        if parsed:
            return parsed, "jsonld"

    raw = jsonld_raw_field(response, "datePosted", "datePublished", "dateCreated")
    if raw:
        parsed = parse_date_text(raw, today=today)
        if parsed:
            return parsed, "jsonld-raw"

    for xp in (
        '//meta[@property="article:published_time"]/@content',
        '//meta[@itemprop="datePosted"]/@content',
        '//meta[@name="date"]/@content',
    ):
        raw = response.xpath(xp).get()
        if raw:
            parsed = parse_date_text(raw, today=today)
            if parsed:
                return parsed, "meta"

    for raw in response.xpath("//time/@datetime").getall():
        parsed = parse_date_text(raw, today=today)
        if parsed:
            return parsed, "time-attr"

    for raw in response.xpath("//time//text()").getall():
        parsed = parse_date_text(raw, today=today)
        if parsed:
            return parsed, "time-text"

    for raw in response.xpath(
        '//*[contains(translate(@class,"DATEPOS","datepos"),"date")'
        ' or contains(translate(@class,"DATEPOS","datepos"),"posted")]//text()'
    ).getall():
        parsed = parse_date_text(raw, today=today)
        if parsed:
            return parsed, "class-hint"

    return None, "none"


def discover_links(response, pattern, hint_selectors=()):
    """Absolute URLs on the page whose path matches pattern.

    hint_selectors narrow the search when they still match; when they match
    nothing the whole page is scanned instead, so a container class being
    renamed costs precision but never drops to zero.
    """
    compiled = re.compile(pattern)
    scoped = []
    for selector in hint_selectors:
        found = response.xpath(selector).getall()
        if found:
            scoped = found
            break
    if not scoped:
        scoped = response.xpath("//a/@href").getall()

    urls = []
    for href in scoped:
        if not href or href.startswith(("mailto:", "javascript:", "#")):
            continue
        absolute = urljoin(response.url, href.strip())
        if compiled.search(urlparse(absolute).path) and absolute not in urls:
            urls.append(absolute)
    return urls
