# Contributing

This is a personal collection of lead-generation spiders, not a maintained library, but fixes
and additions are welcome.

## Setup

```bash
uv sync
uv run scrapy list
```

## Before opening a PR

- `uv run scrapy list` must succeed and print all spider names.
- New or changed spiders should include a note on which site markup they were tested against
  and the date, since these selectors go stale as sites change their HTML.
- Keep one keyword list and one settings module; don't reintroduce per-spider copies.

## Reporting a broken spider

Open an issue with the spider name and the site's current markup for the section it can no
longer find (a saved HTML snippet or a link is enough). These are XPath-driven and will drift
as sites redesign.
