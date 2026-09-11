<!-- repo-header:start -->
<h3 align="center">Scrapy-Spiders</h3>

<p align="center"><strong>Collection of python scripts I have created to crawl various websites, mostly for lead generation projects to match keywords and collect email addresses and post URLs</strong></p>

<p align="center">
  <a href=".bestpractices.json"><img src="https://img.shields.io/badge/best%20practices-evidence%20reviewed-6a4c93?style=flat-square&labelColor=20232a" alt="Best Practices Evidence"></a>
  <a href="https://github.com/dcondrey/scrapy-spiders/blob/master/LICENSE"><img src="https://img.shields.io/github/license/dcondrey/scrapy-spiders?style=flat-square&labelColor=20232a&color=007ec6&label=license" alt="License"></a>
  <a href="https://github.com/sponsors/dcondrey"><img src="https://img.shields.io/badge/GitHub%20Sponsors-Sponsor-EA4AAA?style=flat-square&labelColor=20232a" alt="GitHub Sponsors"></a>
</p>
<!-- repo-header:end -->

---

A set of Scrapy crawlers written for lead-generation work: each one walks a job or production
listing site, matches posts against keywords, and collects contact email addresses along with
the URL of the post they came from.

## The spiders

One Scrapy project, `scrapyspiders/`, with five spiders:

| Spider name | Site |
|---|---|
| `craiglist` | Craigslist |
| `mandy` | Mandy.com (film and TV crew) |
| `entertainmentcareers` | EntertainmentCareers.net |
| `productionhub` | ProductionHub |
| `newenglandfilm` | NewEnglandFilm.com |

Each spider yields an `EmailLeadItem` (`email`, `source_url`, `spider`); a pipeline
(`scrapyspiders/pipelines.py`) dedupes against `<spider name>.txt` and appends new
addresses to it.

## Run one

```bash
uv sync
uv run scrapy crawl <spider-name> -o results.json
```

`uv run scrapy list` prints the five spider names.

## Dependencies

- Python >= 3.10
- [Scrapy](https://github.com/scrapy/scrapy/) 2.19+, pinned in `pyproject.toml` / `uv.lock`

## Status

Ported from a Python 2.7 / pre-2015 Scrapy codebase to run on current Python and Scrapy.
`scrapy list` importing all five spiders is the only thing verified; the XPath selectors
target each site's markup as it existed years ago and are unverified against the current
pages -- treat them as a starting point, not as something that still returns results
unmodified. Check each site's terms of service and `robots.txt` before pointing a crawler
at it.
