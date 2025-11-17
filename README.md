# rss-feeds

Automated RSS feed generation using GitHub Workflows. This repository runs scheduled scrapers, transforms fetched HTML into structured feed data, and publishes RSS files.

## Project structure

- `amd/` — AMD Gaming-specific code and assets
  - `amd/models.py` — Pydantic models for AMD promotions
  - `amd/scrapers.py` — AMD Gaming scraper implementation
  - `amd/amd_gaming_promotions.rss` — generated RSS feed output
- `feed_generator.py` — generic RSS 2.0 feed generator
- `main.py` — entry point orchestrating scraping and feed generation

## Run locally

```bash
uv sync
uv run python main.py
```

The generated file will be written to `amd/amd_gaming_promotions.rss`.
