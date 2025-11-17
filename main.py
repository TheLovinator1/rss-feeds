"""RSS feed generation entry point."""

import html
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
    rss_xml: str = generator.generate_feed(promotions, build_amd_promotion_description)

    # Save RSS feed
    output_path: Path = Path("pages/amd_gaming_promotions.rss")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rss_xml, encoding="utf-8")

    logger.success(f"RSS feed generated: {output_path.absolute()}")


if __name__ == "__main__":
    main()
