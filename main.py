"""RSS feed generation entry point."""

import html
import re
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

from loguru import logger

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
    match = re.search(r"<lastBuildDate>([^<]+)</lastBuildDate>", rss_content)
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

    Removes lastBuildDate, keysAvailable counts, and normalizes line endings
    since they change frequently but don't represent meaningful content changes.

    Args:
        content: RSS XML content

    Returns:
        Normalized content without dynamic elements
    """
    # Remove lastBuildDate
    content = re.sub(r"<lastBuildDate>[^<]+</lastBuildDate>", "", content)
    # Remove keysAvailable counts (e.g., "9514 keys Available:")
    content = re.sub(r"\d+ keys Available:", "keys Available:", content)
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
        description_parts.append(f'<img src="{html.escape(promo.local_image_path)}" alt="{html.escape(promo.title)}"/><br/>')

    description_parts.extend([
        f"<p>{content}</p>",
        f"<p><strong>Platform:</strong> {html.escape(promo.platform)}</p>",
        f"<p><strong>Developer:</strong> {html.escape(promo.developer)}</p>",
        f"<p><strong>{promo.keys_available} keys Available:</strong></p>",
    ])

    if promo.youtube_url:
        description_parts.append(f'<p><a href="{html.escape(promo.youtube_url)}">Watch Trailer</a></p>')

    return "".join(description_parts)


def main() -> None:
    """Fetch promotions and generate RSS feeds."""
    logger.info("Starting RSS feed generation")

    # Fetch promotions
    scraper: AMDGamingScraper = AMDGamingScraper()
    promotions: PromotionsResponse = scraper.fetch_promotions()

    logger.info(f"Processing {len(promotions.items)} promotions")

    # Download images and update promotion items with local paths
    downloader: ImageDownloader = ImageDownloader()
    for promotion in promotions.items:
        local_path: Path | None = downloader.download_image(promotion.thumbnail_image_url, promotion.id)
        if local_path:
            # Convert to GitHub Pages URL
            promotion.local_image_path = downloader.get_github_pages_url(local_path)
            logger.debug(f"Set local image path for {promotion.title}: {promotion.local_image_path}")

    # Generate RSS feed
    generator: RSSFeedGenerator = RSSFeedGenerator(
        channel_title="AMD Gaming Promotions",
        channel_link="https://www.amdgaming.com/promotions",
        channel_description="Free game giveaways and promotions from AMD Gaming",
    )

    # Check for existing feed and detect changes
    output_path: Path = Path("pages/amd_gaming_promotions.rss")

    # Always generate with current timestamp
    rss_xml: str = generator.generate_feed(promotions, build_amd_promotion_description, datetime.now(UTC))

    # Compare normalized content if existing feed exists
    if output_path.exists():
        existing_content: str = output_path.read_text(encoding="utf-8")
        existing_last_build_date: datetime | None = extract_last_build_date(existing_content)
        logger.debug(f"Found existing feed with lastBuildDate: {existing_last_build_date}")

        existing_normalized: str = normalize_rss_content(existing_content)
        new_normalized: str = normalize_rss_content(rss_xml)

        if existing_normalized == new_normalized:
            logger.info("No changes detected in feed content - skipping write")
            return

        logger.info("Changes detected in feed content - updating feed")

    # Save RSS feed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rss_xml, encoding="utf-8")

    logger.success(f"RSS feed generated: {output_path.absolute()}")


if __name__ == "__main__":
    main()
