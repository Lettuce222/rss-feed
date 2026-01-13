import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import pytest

from app.config import FeedConfig
from app.feed_builder import FeedBuilder
from app.models import NormalizedItem


class TestFeedBuilder:
    """Tests for RSS feed generation."""

    @pytest.fixture
    def feed_config(self):
        return FeedConfig(
            title="Test Feed",
            description="Test feed description",
            link="https://example.com/feed.xml",
            language="en",
            max_items=10,
        )

    @pytest.fixture
    def sample_items(self):
        return [
            NormalizedItem(
                source_id="source_a",
                source_display_name="Source A",
                title="Item 1",
                url="https://example.com/1",
                published_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
                description="Description 1",
            ),
            NormalizedItem(
                source_id="source_b",
                source_display_name="Source B",
                title="Item 2",
                url="https://example.com/2",
                published_at=datetime(2024, 1, 14, 8, 0, 0, tzinfo=UTC),
                description="Description 2",
            ),
            NormalizedItem(
                source_id="source_a",
                source_display_name="Source A",
                title="Item 3",
                url="https://example.com/3",
                published_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
                description=None,
            ),
        ]

    def test_build_returns_valid_xml(self, feed_config, sample_items):
        builder = FeedBuilder(feed_config)
        xml_str = builder.build(sample_items)

        # Should start with XML declaration
        assert xml_str.startswith('<?xml version="1.0" encoding="UTF-8"?>')

        # Should be parseable
        root = ET.fromstring(xml_str.split("\n", 1)[1])  # Remove XML declaration
        assert root.tag == "rss"
        assert root.get("version") == "2.0"

    def test_channel_metadata(self, feed_config, sample_items):
        builder = FeedBuilder(feed_config)
        xml_str = builder.build(sample_items)

        root = ET.fromstring(xml_str.split("\n", 1)[1])
        channel = root.find("channel")

        assert channel.find("title").text == "Test Feed"
        assert channel.find("link").text == "https://example.com/feed.xml"
        assert channel.find("description").text == "Test feed description"
        assert channel.find("language").text == "en"
        assert channel.find("lastBuildDate") is not None

    def test_items_are_sorted_by_date_descending(self, feed_config, sample_items):
        builder = FeedBuilder(feed_config)
        xml_str = builder.build(sample_items)

        root = ET.fromstring(xml_str.split("\n", 1)[1])
        channel = root.find("channel")
        items = channel.findall("item")

        # Item 3 (Jan 16) should be first
        assert items[0].find("title").text == "Item 3"
        # Item 1 (Jan 15) should be second
        assert items[1].find("title").text == "Item 1"
        # Item 2 (Jan 14) should be third
        assert items[2].find("title").text == "Item 2"

    def test_max_items_limit(self, feed_config):
        # Create more items than max_items
        items = [
            NormalizedItem(
                source_id="source",
                source_display_name="Source",
                title=f"Item {i}",
                url=f"https://example.com/{i}",
                published_at=datetime(2024, 1, i + 1, 0, 0, 0, tzinfo=UTC),
                description=f"Description {i}",
            )
            for i in range(20)
        ]

        feed_config.max_items = 5
        builder = FeedBuilder(feed_config)
        xml_str = builder.build(items)

        root = ET.fromstring(xml_str.split("\n", 1)[1])
        channel = root.find("channel")
        result_items = channel.findall("item")

        assert len(result_items) == 5

    def test_item_fields(self, feed_config, sample_items):
        builder = FeedBuilder(feed_config)
        source_urls = {"source_a": "https://source-a.com/feed"}
        xml_str = builder.build(sample_items, source_urls)

        root = ET.fromstring(xml_str.split("\n", 1)[1])
        channel = root.find("channel")
        first_item = channel.findall("item")[0]  # Item 3 (most recent)

        assert first_item.find("title").text == "Item 3"
        assert first_item.find("link").text == "https://example.com/3"
        # description should fall back to source_display_name when None
        assert first_item.find("description").text == "Source A"
        assert first_item.find("guid").text == "https://example.com/3"
        assert first_item.find("guid").get("isPermaLink") == "true"
        assert first_item.find("pubDate") is not None

    def test_source_element(self, feed_config, sample_items):
        builder = FeedBuilder(feed_config)
        source_urls = {
            "source_a": "https://source-a.com/feed",
            "source_b": "https://source-b.com/feed",
        }
        xml_str = builder.build(sample_items, source_urls)

        root = ET.fromstring(xml_str.split("\n", 1)[1])
        channel = root.find("channel")
        items = channel.findall("item")

        # Check source element for first item (Item 3 from source_a)
        source_elem = items[0].find("source")
        assert source_elem is not None
        assert source_elem.text == "Source A"
        assert source_elem.get("url") == "https://source-a.com/feed"

    def test_empty_items_list(self, feed_config):
        builder = FeedBuilder(feed_config)
        xml_str = builder.build([])

        root = ET.fromstring(xml_str.split("\n", 1)[1])
        channel = root.find("channel")
        items = channel.findall("item")

        assert len(items) == 0
        # Channel metadata should still be present
        assert channel.find("title").text == "Test Feed"
