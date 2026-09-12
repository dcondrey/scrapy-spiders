"""Detect anti-bot interstitials and say so, once, in plain terms.

A challenge page returns a valid HTTP response containing no listings, which
otherwise looks identical to "the selectors broke". Naming the vendor turns a
silent empty crawl into an actionable message.
"""

import re

CHALLENGE_SIGNATURES = (
    (
        "Cloudflare",
        re.compile(
            r"just a moment|attention required|cf-browser-verification"
            r"|challenge-platform|cf_chl_opt",
            re.I,
        ),
    ),
    ("DataDome", re.compile(r"datadome|dd_cookie_test", re.I)),
    ("PerimeterX", re.compile(r"perimeterx|_px(?:2|3|Captcha)", re.I)),
    ("Akamai", re.compile(r"ak_bmsc|_abck|akamai bot manager", re.I)),
    ("hCaptcha/reCAPTCHA", re.compile(r"hcaptcha\.com|recaptcha/api\.js", re.I)),
)

BLOCKED_STATUSES = {401, 403, 406, 429, 503}


class BotChallengeDetectionMiddleware:
    """Log a clear, deduplicated diagnosis when a host serves a challenge."""

    def __init__(self):
        self.reported = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_response(self, request, response, spider):
        host = request.url.split("/")[2] if "//" in request.url else request.url
        if host in self.reported:
            return response

        vendor = self.identify(response)
        if vendor is None and response.status not in BLOCKED_STATUSES:
            return response
        if vendor is None:
            return response

        self.reported.add(host)
        spider.logger.error(
            "%s is served by a %s anti-bot challenge (HTTP %d). Scrapy cannot "
            "solve it with plain HTTP requests. Options: use a browser engine "
            "(scrapy-playwright), use an official API or data feed if one "
            "exists, or drop this source. This is not a selector problem.",
            host,
            vendor,
            response.status,
        )
        return response

    def identify(self, response):
        body = response.text[:20000] if hasattr(response, "text") else ""
        for vendor, pattern in CHALLENGE_SIGNATURES:
            if pattern.search(body):
                return vendor
        server = response.headers.get("Server", b"").decode("latin-1", "ignore")
        if "cloudflare" in server.lower() and response.status in BLOCKED_STATUSES:
            return "Cloudflare"
        return None
