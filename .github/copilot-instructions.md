# RSS Feeds Project - AI Agent Instructions

## Project Overview
Automated RSS feed generation system designed to run scheduled scrapers via GitHub Workflows, transform HTML into structured feed data, and publish RSS files.

## Technology Stack
- **Python**: 3.14+ (specified in `.python-version`)
- **Package Manager**: `uv` (fast Python package installer, replaces pip/poetry)
- **Dependencies**: curl-cffi (HTTP requests), loguru (logging), pydantic (data validation)
- **Linter/Formatter**: Ruff with preview features enabled

## Development Environment Setup
```bash
# Install dependencies using uv (preferred over pip)
uv sync

# Add new dependencies
uv add <package-name>

# Add dev dependencies
uv add --dev <package-name>

# Run the application
uv run main.py
```

## Code Style & Conventions

### Logging
- Use `loguru` for all logging (already imported in `main.py`)
- Import: `from loguru import logger`
- No need for manual logger configuration - loguru provides sensible defaults

### Ruff Configuration
- **Line length**: 160 characters (not the standard 88/120)
- **Import style**: Force single-line imports (`force-single-line = true`)
- **Docstrings**: Google style convention
- **All rules enabled** with specific ignores - check `pyproject.toml` for exceptions
- Key ignored rules:
  - Return type annotations for public functions (ANN201)
  - Commented-out code (ERA001)
  - TODO comments without issue links (TD003)
  - Class variables in mixedCase (N815)

### Testing
- Framework: pytest (in dev dependencies)
- Test files exempt from: docstring requirements (D103), assert usage (S101), magic numbers (PLR2004)

## Project Structure
```
main.py              # Entry point - orchestrates scraping and feed generation
feed_generator.py    # RSS 2.0 XML generation
pages/               # Output directory for .rss feeds (GitHub Pages)
  amd_gaming_promotions.rss  # Generated AMD Gaming promotions feed
pyproject.toml       # Dependencies, Ruff config, project metadata
README.md            # Project documentation
.github/             # GitHub Workflows
amd/                 # AMD Gaming-specific code and assets
  __init__.py        # Package initialization
  models.py          # Pydantic models for AMD promotions
  scrapers.py        # AMD Gaming scraper implementation
```

## Architecture Patterns

### Scraper Pattern
Each site gets a dedicated scraper class (see `AMDGamingScraper`):
- Use curl-cffi's `requests.Session()` for persistent connections
- Set `impersonate="chrome"` to mimic browser TLS fingerprints
- Include realistic headers (User-Agent, Referer, Sec-Fetch-* headers)
- Return Pydantic-validated data models, not raw dicts
- Let exceptions bubble up - validation errors are useful

### Data Flow
1. **Scraper** fetches JSON/HTML → validates with Pydantic → returns typed model
2. **Feed Generator** transforms model → RSS 2.0 XML with proper escaping
3. **Main** orchestrates: scrape → generate → write to `pages/` directory for GitHub Pages

### RSS Generation
- Use `xml.etree.ElementTree` (with S405 exception - we control the input)
- HTML content in descriptions must be escaped with `html.escape()`
- Use RFC 822 date format for `<pubDate>` and `<lastBuildDate>`
- GUIDs use internal IDs (not permalinks) for stability

## Common Workflows
```bash
# Run the scraper and generate feeds
uv run main.py

# Run tests
uv run pytest

# Lint with Ruff
ruff check .

# Format with Ruff
ruff format .
```

## Type Checking Notes
- curl-cffi has incomplete type stubs - expect `Unknown` type warnings
- Use `TYPE_CHECKING` blocks for imports only needed for type hints
- xml.etree usage requires `# noqa: S405` (we control input, XML attacks not applicable)

## Adding New Scrapers
1. Create model in `models.py` matching API response structure
2. Add scraper class in `scrapers.py` with proper headers and impersonation
3. Test data validation with actual API responses
4. Update `main.py` to include new scraper in feed generation
5. Save RSS output to `pages/` directory for GitHub Pages deployment
6. Use descriptive class names: `{Site}Scraper` pattern

## Important Notes
- GitHub Workflows will be the primary execution environment (not yet implemented)
- Focus on curl-cffi for HTTP requests (handles anti-bot measures better than requests)
- All new code must follow the strict Ruff configuration in `pyproject.toml`
- Prefer single-line imports (force-single-line = true)
