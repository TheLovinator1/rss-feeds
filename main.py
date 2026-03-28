"""RSS feed generation entry point."""

import html
import json
import re
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

from loguru import logger

from amd.csv_logger import append_keys_data_to_csv
from amd.image_downloader import ImageDownloader
from amd.scrapers import AMDGamingScraper
from feed_generator import RSSFeedGenerator

if TYPE_CHECKING:
    from amd.models import PromotionItem
    from amd.models import PromotionsResponse
    from feed_generator import FeedItem


def extract_last_build_date(rss_content: str) -> datetime | None:
    """Extract lastBuildDate from existing RSS feed.

    Args:
        rss_content: RSS XML content as string

    Returns:
        Parsed datetime or None if not found/invalid
    """
    match: re.Match[str] | None = re.search(r"<lastBuildDate>([^<]+)</lastBuildDate>", rss_content)
    if not match:
        return None

    try:
        # Parse RFC 822 format: "Mon, 17 Nov 2025 10:37:41 +0000"
        return datetime.strptime(match.group(1), "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        logger.warning(f"Failed to parse lastBuildDate: {match.group(1)}")
        return None


def normalize_rss_content(content: str) -> str:
    """Normalize RSS content for comparison by removing dynamic elements.

    Removes lastBuildDate and normalizes line endings since they change frequently
    but don't represent meaningful content changes.

    Args:
        content: RSS XML content

    Returns:
        Normalized content without dynamic elements
    """
    # Remove lastBuildDate
    content = re.sub(r"<lastBuildDate>[^<]+</lastBuildDate>", "", content)
    # Normalize line endings (API returns \r\n, but file may have \n)
    return content.replace("\r\n", "\n")


def build_amd_promotion_description(item: FeedItem) -> str:
    """Build rich HTML description for AMD Gaming promotions.

    Args:
        item: Feed item (should be a PromotionItem)

    Returns:
        HTML description string with thumbnail, content, and metadata
    """
    # Cast to PromotionItem to access AMD-specific fields
    promo: PromotionItem = cast("PromotionItem", item)

    # Escape HTML content to prevent malformed XML
    content: str = html.escape(promo.content)

    # Build description with optional thumbnail, content, and availability
    description_parts: list[str] = []

    # Add image only if available
    if promo.local_image_path:
        html_img: str = f'<img src="{html.escape(promo.local_image_path)}" alt="{html.escape(promo.title)}" style="max-width: 100%; height: auto;"/><br/>'
        description_parts.append(html_img)

    # Main content
    description_parts.extend((
        f"<p>{content}</p>",
        f"<p><strong>Platform:</strong> {html.escape(promo.platform)} | <strong>Developer:</strong> {html.escape(promo.developer)}</p>",
    ))

    # Action links section
    links: list[str] = [f'<a href="https://www.amdgaming.com/promotions/{html.escape(promo.slug)}">Claim</a>']

    if promo.youtube_url:
        links.append(f'<a href="{html.escape(promo.youtube_url)}">Trailer</a>')

    links.append('<a href="https://www.amdgaming.com/promotions">Promotions</a>')

    description_parts.append("<p>" + " • ".join(links) + "</p>")

    return "".join(description_parts)


def main() -> None:
    """Fetch promotions and generate RSS feeds, with restock detection for dev feed."""
    logger.info("Starting RSS feed generation (with restock detection)")

    # Fetch promotions
    scraper: AMDGamingScraper = AMDGamingScraper()
    promotions: PromotionsResponse = scraper.fetch_promotions()

    logger.info(f"Processing {len(promotions.items)} promotions")

    # Log keys availability to CSV for tracking
    json_path: Path = Path("pages/data/amd_response.json")
    csv_path: Path = Path("pages/data/amd_gaming_keys_available.csv")
    append_keys_data_to_csv(json_path, csv_path)
    logger.info("Logged keys availability to CSV")

    # Download images and update promotion items with local paths
    downloader: ImageDownloader = ImageDownloader()
    for promotion in promotions.items:
        local_path: Path | None = downloader.download_image(promotion.thumbnail_image_url, promotion.id)
        if local_path:
            # Convert to GitHub Pages URL
            promotion.local_image_path = downloader.get_github_pages_url(local_path)
            logger.debug(f"Set local image path for {promotion.title}: {promotion.local_image_path}")

    # --- Restock detection logic ---
    restock_state_path: Path = Path("pages/data/amd_gaming_keys_restock_state.json")
    restock_state: dict[str, dict[str, int]] = {"promotions": {}}
    if restock_state_path.exists():
        try:
            with restock_state_path.open("r", encoding="utf-8") as f:
                restock_state = json.load(f)
        except (TypeError, OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load restock state: {e}")

    prev_keys: dict[str, int] = restock_state.get("promotions", {})
    restocked: list[str] = []
    new_keys: dict[str, int] = {}
    for promo in promotions.items:
        prev: int = prev_keys.get(promo.id, 0)
        new_keys[promo.id] = promo.keys_available
        if prev == 0 and promo.keys_available > 0:
            restocked.append(promo.id)

    # Save new state
    try:
        with restock_state_path.open("w", encoding="utf-8") as f:
            json.dump({"promotions": new_keys}, f, indent=2)
    except (OSError, TypeError) as e:
        logger.warning(f"Failed to save restock state: {e}")

    # --- Feed generation ---
    generator: RSSFeedGenerator = RSSFeedGenerator(
        channel_title="AMD Gaming Promotions (DEV)",
        channel_link="https://www.amdgaming.com/promotions",
        channel_description="[DEV FEED] Free game giveaways and promotions from AMD Gaming",
    )

    dev_output_path: Path = Path("pages/amd_gaming_promotions_dev.xml")
    rss_xml: str = generator.generate_feed(promotions, build_amd_promotion_description, datetime.now(UTC))

    # Only write dev feed if any restock detected
    if restocked:
        logger.info(f"Restock detected for promotions: {restocked} - writing DEV feed")
        dev_output_path.parent.mkdir(parents=True, exist_ok=True)
        dev_output_path.write_text(rss_xml, encoding="utf-8")
        logger.success(f"DEV RSS feed generated: {dev_output_path.absolute()}")
    else:
        logger.info("No restock detected - DEV feed not updated")


if __name__ == "__main__":
    main()
