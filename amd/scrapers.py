"""Scrapers for fetching AMD Gaming promotional data."""

import json
from pathlib import Path
from typing import Any
from typing import LiteralString

from curl_cffi import requests
from loguru import logger

from .models import PromotionsResponse


class AMDGamingScraper:
    """Scraper for AMD Gaming promotions and giveaways.

    Fetches active game giveaways from amdgaming.com using curl-cffi
    to handle anti-bot protections. The site uses Discourse forum software
    and requires specific headers including CSRF tokens for authenticated requests.

    Note: The current implementation uses headers from an authenticated session.
    For public giveaways, authentication may not be required - test both approaches.
    """

    def __init__(self) -> None:
        """Initialize the scraper."""
        self.session: requests.Session[requests.Response] = requests.Session()

    def fetch_promotions(self, *, save_response: bool = True) -> PromotionsResponse:
        """Fetch all active promotions from AMD Gaming.

        Args:
            save_response: Whether to save the raw API response for git tracking (default: True)

        Returns:
            PromotionsResponse containing list of promotion items
        """
        url: LiteralString = "https://www.amdgaming.com/promotions"

        headers: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.7,sv;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.amdgaming.com/promotions",
            "X-Requested-With": "XMLHttpRequest",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        logger.info(f"Fetching promotions from {url}")

        response: requests.Response = self.session.get(url, headers=headers, impersonate="firefox")
        response.raise_for_status()

        response_data: dict[str, Any] = response.json()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

        # Save raw response for git history tracking
        if save_response:
            self.save_response(response_data)  # pyright: ignore[reportUnknownArgumentType]

        result: PromotionsResponse = PromotionsResponse.model_validate(response_data)
        logger.info(f"Successfully fetched {len(result.items)} promotions")

        return result

    def save_response(self, response_data: dict[str, Any], output_dir: Path = Path("pages/data")) -> Path:
        """Save raw API response to a file for git history tracking.

        Args:
            response_data: The raw JSON response from the API
            output_dir: Directory to save the response file (default: pages/data/)

        Returns:
            Path to the saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        filename: Path = output_dir / "amd_response.json"

        with filename.open("w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=4, ensure_ascii=False, sort_keys=True)

        logger.info(f"Saved API response to {filename}")
        return filename
