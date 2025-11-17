"""RSS feed generation from any structured data.

This module provides a generic RSS 2.0 feed generator that works with any data source
by using Protocol-based interfaces. To create feeds for a new data source:

1. Implement FeedItem protocol in your model by adding these properties:
   - feed_id: str - Unique identifier
   - feed_title: str - Display title
   - feed_link: str - URL link
   - feed_pub_date: datetime - Publication date (timezone-aware)
   - feed_category: str | None - Optional category/tags

2. Implement FeedCollection protocol with:
   - items: Sequence[FeedItem] - Your collection of items

3. Create a description builder function with signature:
   def build_description(item: FeedItem) -> str:
       # Return HTML description for RSS item

4. Pass your collection and description builder to RSSFeedGenerator.generate_feed()

Example:
    generator = RSSFeedGenerator(
        channel_title="My Feed",
        channel_link="https://example.com",
        channel_description="Feed description"
    )
    rss_xml = generator.generate_feed(my_collection, my_description_builder)
"""

from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import LiteralString
from typing import Protocol
from typing import runtime_checkable
from xml.etree import ElementTree as ET  # noqa: S405

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Sequence


@runtime_checkable
class FeedItem(Protocol):
    """Protocol defining the interface for feed items.

    Any object that implements these properties can be used with RSSFeedGenerator.
    """

    @property
    def feed_id(self) -> str:
        """Unique identifier for the feed item."""
        ...

    @property
    def feed_title(self) -> str:
        """Display title of the feed item."""
        ...

    @property
    def feed_link(self) -> str:
        """URL link for the feed item."""
        ...

    @property
    def feed_pub_date(self) -> datetime:
        """Publication date of the feed item (timezone-aware)."""
        ...

    @property
    def feed_category(self) -> str | None:
        """Optional category/tags for the feed item."""
        ...


@runtime_checkable
class FeedCollection(Protocol):
    """Protocol defining a collection of feed items."""

    @property
    def items(self) -> Sequence[FeedItem]:
        """Sequence of feed items."""
        ...


class RSSFeedGenerator:
    """Generate RSS 2.0 feeds from promotional data.

    Creates valid RSS XML with proper encoding, CDATA sections for HTML content,
    and all required channel/item elements per RSS 2.0 specification.
    """

    def __init__(self, channel_title: str, channel_link: str, channel_description: str) -> None:
        """Initialize RSS feed generator with channel metadata.

        Args:
            channel_title: The name of the RSS channel
            channel_link: URL to the channel's website
            channel_description: Brief description of the channel content
        """
        self.channel_title: str = channel_title
        self.channel_link: str = channel_link
        self.channel_description: str = channel_description

    def generate_feed(
        self,
        feed_collection: FeedCollection,
        description_builder: Callable[[FeedItem], str],
        last_build_date: datetime | None = None,
    ) -> str:
        """Generate RSS 2.0 XML feed from feed items.

        Args:
            feed_collection: Collection containing list of feed items
            description_builder: Callback function to build HTML description for each item
            last_build_date: Optional existing lastBuildDate to preserve when content hasn't changed

        Returns:
            RSS 2.0 XML feed as a string
        """
        rss: ET.Element[str] = ET.Element("rss", version="2.0")
        channel: ET.Element[str] = ET.SubElement(rss, "channel")

        # Channel metadata
        ET.SubElement(channel, "title").text = self.channel_title
        ET.SubElement(channel, "link").text = self.channel_link
        ET.SubElement(channel, "description").text = self.channel_description
        build_date: datetime = last_build_date or datetime.now(UTC)
        ET.SubElement(channel, "lastBuildDate").text = self._format_rfc822_date(build_date)

        # Add items
        for item in feed_collection.items:
            self._add_item(channel, item, description_builder)

        # Pretty print XML
        self._indent_xml(rss)
        return ET.tostring(rss, encoding="unicode", method="xml")

    def _add_item(self, channel: ET.Element, feed_item: FeedItem, description_builder: Callable[[FeedItem], str]) -> None:
        """Add a single feed item as an RSS item.

        Args:
            channel: The RSS channel element to add the item to
            feed_item: Feed item data to convert to RSS item
            description_builder: Callback to build HTML description
        """
        item: ET.Element[str] = ET.SubElement(channel, "item")

        # Required RSS elements
        ET.SubElement(item, "title").text = feed_item.feed_title
        ET.SubElement(item, "link").text = feed_item.feed_link
        ET.SubElement(item, "guid", isPermaLink="false").text = feed_item.feed_id

        # Description with rich HTML content
        description: str = description_builder(feed_item)
        ET.SubElement(item, "description").text = description

        # Publication date
        ET.SubElement(item, "pubDate").text = self._format_rfc822_date(feed_item.feed_pub_date)

        # Optional category
        if feed_item.feed_category:
            ET.SubElement(item, "category").text = feed_item.feed_category

    @staticmethod
    def _format_rfc822_date(dt: datetime) -> str:
        """Format datetime as RFC 822 (required by RSS 2.0).

        Args:
            dt: Datetime to format (should be timezone-aware)

        Returns:
            RFC 822 formatted date string
        """
        return dt.strftime("%a, %d %b %Y %H:%M:%S %z")

    @staticmethod
    def _indent_xml(elem: ET.Element, level: int = 0) -> None:
        """Add pretty-printing indentation to XML tree in-place.

        Args:
            elem: XML element to indent
            level: Current indentation level
        """
        indent_str: LiteralString = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent_str + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent_str
            last_child: ET.Element[str] | None = None
            for child in elem:
                RSSFeedGenerator._indent_xml(child, level + 1)
                last_child = child
            if last_child is not None and (not last_child.tail or not last_child.tail.strip()):
                last_child.tail = indent_str
        elif level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent_str
