from datetime import UTC, datetime
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from app.config import FeedConfig
from app.models import NormalizedItem


class FeedBuilder:
    """Builder for RSS 2.0 feed from normalized items."""

    def __init__(self, config: FeedConfig):
        self.config = config

    def build(
        self,
        items: list[NormalizedItem],
        source_urls: dict[str, str] | None = None,
    ) -> str:
        """Build RSS 2.0 feed XML string from normalized items.

        Args:
            items: List of normalized items to include in the feed.
            source_urls: Mapping of source_id to source URL for <source> element.

        Returns:
            RSS 2.0 XML string.
        """
        source_urls = source_urls or {}

        # Sort by published_at descending
        sorted_items = sorted(items, key=lambda x: x.published_at, reverse=True)

        # Limit to max_items
        limited_items = sorted_items[: self.config.max_items]

        # Build XML
        rss = Element("rss", version="2.0")
        channel = SubElement(rss, "channel")

        # Channel metadata
        SubElement(channel, "title").text = self.config.title
        SubElement(channel, "link").text = self.config.link
        SubElement(channel, "description").text = self.config.description
        SubElement(channel, "language").text = self.config.language

        # Last build date
        now = datetime.now(UTC)
        SubElement(channel, "lastBuildDate").text = format_datetime(now)

        # Items
        for item in limited_items:
            item_elem = SubElement(channel, "item")
            SubElement(item_elem, "title").text = item.title
            SubElement(item_elem, "link").text = item.url
            SubElement(item_elem, "description").text = (
                item.description or item.source_display_name
            )
            SubElement(item_elem, "pubDate").text = format_datetime(item.published_at)
            guid = SubElement(item_elem, "guid", isPermaLink="true")
            guid.text = item.url

            # Source element
            source_url = source_urls.get(item.source_id, "")
            if source_url:
                source_elem = SubElement(item_elem, "source", url=source_url)
                source_elem.text = item.source_display_name

        # Convert to string with XML declaration
        xml_str = tostring(rss, encoding="unicode")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
