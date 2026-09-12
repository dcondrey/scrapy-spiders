<!-- repo-header:start -->
<h3 align="center">Scrapy-Spiders</h3>

<p align="center"><strong>Scrapy crawlers that collect film and TV production job listings from industry job boards</strong></p>

<p align="center">
  <a href="https://github.com/dcondrey/scrapy-spiders/actions"><img src="https://img.shields.io/github/actions/workflow/status/dcondrey/scrapy-spiders/ci.yml?style=flat-square&labelColor=20232a&label=CI" alt="CI"></a>
  <a href="https://github.com/dcondrey/scrapy-spiders/blob/master/LICENSE"><img src="https://img.shields.io/github/license/dcondrey/scrapy-spiders?style=flat-square&labelColor=20232a&color=007ec6&label=license" alt="License"></a>
  <a href="https://github.com/sponsors/dcondrey"><img src="https://img.shields.io/badge/GitHub%20Sponsors-Sponsor-EA4AAA?style=flat-square&labelColor=20232a" alt="GitHub Sponsors"></a>
</p>
<!-- repo-header:end -->

---

A single Scrapy project that walks film and TV production job boards, keeps postings matching
a keyword list, and records title, company, location, posting date, source URL, and a contact
email when the page exposes one.

## Source status

Checked live on 2026-09-11. Run `uv run python scripts/check_sources.py` to recheck.

| Spider | Site | Status |
|---|---|---|
| `entertainmentcareers` | EntertainmentCareers.net | **Working.** Keyword search; fields from schema.org JobPosting. |
| `craiglist` | Craigslist | **Working.** Driven by the public posting sitemaps. |
| `productionhub` | ProductionHub | **Working with `SCRAPY_IMPERSONATE=1`.** Cloudflare 403s plain clients. |
| `newenglandfilm` | WIFVNE job board | **Working.** Reads the WordPress REST API. Low volume. |
| `mandy` | Mandy.com | Not working. Cloudflare blocks the whole domain including `robots.txt`, and the site is a JavaScript app with no server-rendered links. Needs a browser engine. |

### About emails

Most boards no longer publish employer addresses. Craigslist proxies contact through `/reply`,
which its `robots.txt` disallows. EntertainmentCareers issues a per-listing relay address
(`JOB-<id>-XX@entertainmentcareers.net`) on some postings, which does forward to the employer.
`email` is therefore optional on every item, and the listing data is the primary output.

### Cloudflare and impersonation

ProductionHub rejects ordinary HTTP clients with a 403 no matter the user-agent, because the
block keys on TLS fingerprint. Setting `SCRAPY_IMPERSONATE=1` routes requests through
`curl_cffi`, which presents a real browser fingerprint, and the site then responds normally.

This is off by default and it is your call to enable, because it works around an access control
the operator put in place. Two things worth knowing before you do:

- ProductionHub's `robots.txt` disallows `/jobs/search*`, so this project crawls the
  robots-allowed `/jobs/type/<category>` indexes instead. `ROBOTSTXT_OBEY` stays on with
  impersonation enabled; it does not override a `Disallow`.
- Their `Content-Signal` header permits `search` and `reference` use and forbids `ai-train=no`.

## Run one

```bash
uv sync
uv run scrapy crawl entertainmentcareers -a days=7 -o results.json
uv run scrapy crawl craiglist -a days=2 -a cities=sfo,nyc,lax -o results.json
uv run scrapy crawl newenglandfilm -o results.json
SCRAPY_IMPERSONATE=1 uv run scrapy crawl productionhub -a days=30 -o results.json
```

Spider arguments:

| Argument | Meaning |
|---|---|
| `-a days=N` | Accept postings up to N days old (default 7). |
| `-a max_pages=N` | Index pages to walk per keyword (index-based spiders). |
| `-a cities=sfo,nyc` | Craigslist only. Restrict to these city codes. |
| `-a categories=jjj,ggg` | Craigslist only. Sitemap category codes (jobs, gigs). |

Resume an interrupted crawl with `-s JOBDIR=.jobdirs/<name>`.

## Surviving markup changes

Selector rot is what kills scrapers, so extraction is layered from most durable to least, and
each spider reports which layer actually fired.

1. **Machine-readable metadata first.** schema.org `JobPosting` JSON-LD, then `<meta>`, then
   `<time datetime>`. Sites maintain these for job aggregators, so they outlive redesigns. Every
   field EntertainmentCareers returns currently comes from JSON-LD.
2. **Discovery by URL shape, not DOM position.** Listings are found by matching the href pattern
   (`/<company>/<title>/job/<id>/`), never by `div[3]/p[2]`.
3. **Pattern inference when the pattern misses.** If the configured pattern matches nothing, the
   spider counts the shapes of every link on the page and adopts the dominant repeated family,
   logging the pattern it inferred. This recovers from a URL scheme change, not just a CSS rename.
4. **Feeds and sitemaps as a floor.** An advertised RSS/Atom feed, or the site's sitemap, is a
   format that does not drift. Craigslist is driven this way by default because its search UI is
   JavaScript-only.
5. **Loud diagnosis instead of a silent zero.** Every run logs which strategies fired. Discovering
   zero listings, or fetching pages and yielding nothing, logs an ERROR naming the likely cause.
   A bot challenge is detected and reported by vendor, so "Cloudflare is blocking us" never looks
   like "the selectors broke".

## Tests

```bash
uv run pytest
uv run ruff check .
```

Fixture tests run against unmodified pages captured from the live sites (see
`tests/fixtures/PROVENANCE.md`), so they fail when a site actually redesigns. That failure is the
signal to update the spider. CI also runs a weekly reachability check against every source.

## Dependencies

- Python >= 3.10
- [Scrapy](https://github.com/scrapy/scrapy/) 2.19+, pinned in `pyproject.toml` / `uv.lock`

## Legal

Check each site's terms of service and `robots.txt` before crawling. `ROBOTSTXT_OBEY` is on by
default. Collecting personal contact data may fall under GDPR, CCPA, or similar rules depending
on where you and the subject are.
