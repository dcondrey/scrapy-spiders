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

| Directory | Site |
|---|---|
| `craig` | Craigslist |
| `mandy` | Mandy.com (film and TV crew) |
| `entcareers` | EntertainmentCareers.net |
| `productionhub` | ProductionHub |
| `reelscout` | ReelScout |
| `newenglandfilm` | NewEnglandFilm.com |

Each directory is a self-contained Scrapy project with its own `scrapy.cfg`; several keep the
last run's output alongside it (`outfile.txt` / `output.txt`) as a sample of the shape of the
data.

## Run one

```bash
cd mandy
scrapy crawl <spider-name> -o results.json
```

`scrapy list` inside a project directory prints the spider names it defines.

## Dependencies

- Python 2.7
- [Scrapy](https://github.com/scrapy/scrapy/)

## Status

Archived as written. These target Python 2.7 and the Scrapy API of the time, and the sites they
crawl have all changed their markup since -- treat the selectors as a starting point, not as
something that still runs unmodified. Check each site's terms of service and `robots.txt`
before pointing a crawler at it.
