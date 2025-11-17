"""Data models for RSS feed items (AMD Gaming)."""

from datetime import UTC
from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class PromotionItem(BaseModel):
    """A single promotion/giveaway item from AMD Gaming.

    Represents a game giveaway or promotional offer with all relevant metadata
    including game details, availability, redemption instructions, and media URLs.
    """

    id: str = Field(description="Unique identifier for the promotion")
    title: str = Field(description="Display title of the promotion")
    slug: str = Field(description="URL-friendly identifier")
    content: str = Field(description="Full HTML/markdown description of the promotion")
    game_website_url: str = Field(alias="gameWebsiteUrl", description="Official game store page URL")
    platform: str = Field(description="Gaming platform (Steam, Epic, etc)")
    developer: str = Field(description="Game developer/publisher name")
    thumbnail_image_url: str = Field(alias="thumbnailImageUrl", description="Promotion thumbnail image URL")
    youtube_url: str | None = Field(alias="youtubeUrl", default=None, description="Optional promotional video URL")
    tags: str = Field(description="Comma-separated game genre tags")
    color: str = Field(description="Hex color code for UI theming")
    status: str = Field(description="Promotion status (active, expired, etc)")
    featured: bool = Field(description="Whether this promotion is featured/highlighted")
    keys_available: int = Field(alias="keysAvailable", description="Number of game keys remaining")
    max_keys_per_ip: int = Field(alias="maxKeysPerIp", description="Key claim limit per IP address")
    created_at: int = Field(alias="createdAt", description="Unix timestamp of creation")
    updated_at: int = Field(alias="updatedAt", description="Unix timestamp of last update")
    redemption_instructions: str = Field(alias="redemptionInstructions", description="HTML instructions for key redemption")
    consumer_id: str = Field(alias="consumerId", description="Internal consumer/organization identifier")
    deleted: bool = Field(description="Soft delete flag")

    # Local image path (set after downloading)
    local_image_path: str | None = None

    # FeedItem protocol implementation
    @property
    def feed_id(self) -> str:
        """Unique identifier for the feed item."""
        return self.id

    @property
    def feed_title(self) -> str:
        """Display title of the feed item."""
        return self.title

    @property
    def feed_link(self) -> str:
        """URL link for the feed item."""
        return self.game_website_url

    @property
    def feed_pub_date(self) -> datetime:
        """Publication date of the feed item (timezone-aware)."""
        return datetime.fromtimestamp(self.created_at, tz=UTC)

    @property
    def feed_category(self) -> str | None:
        """Optional category/tags for the feed item."""
        return self.tags


class PromotionsResponse(BaseModel):
    """Response wrapper for AMD Gaming promotions API.

    Contains a list of all active and featured promotions/giveaways.
    """

    items: list[PromotionItem] = Field(description="List of promotion items")
