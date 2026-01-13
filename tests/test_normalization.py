from unittest.mock import MagicMock, patch

import pytest

from app.config import SourceConfig
from app.models import NormalizedItem
from app.sources.generic_rss import GenericRSSFetcher
from app.sources.youtube import YouTubeFetcher


class TestYouTubeFetcher:
    """Tests for YouTube feed normalization."""

    @pytest.fixture
    def youtube_config(self):
        return SourceConfig(
            id="test_youtube",
            type="youtube_channel",
            display_name="Test YouTube Channel",
            enabled=True,
            channel_id="UC123456789",
        )

    @pytest.fixture
    def sample_youtube_feed(self):
        """Sample YouTube Atom feed response."""
        return b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Test Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
    <published>2024-01-15T10:30:00+00:00</published>
    <summary>Test video description</summary>
  </entry>
  <entry>
    <title>Another Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=def456"/>
    <published>2024-01-14T08:00:00+00:00</published>
    <summary>Another description</summary>
  </entry>
</feed>"""

    @patch("app.sources.youtube.requests.get")
    def test_fetch_returns_normalized_items(self, mock_get, youtube_config, sample_youtube_feed):
        mock_response = MagicMock()
        mock_response.content = sample_youtube_feed
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = YouTubeFetcher(youtube_config)
        items = fetcher.fetch()

        assert len(items) == 2
        assert all(isinstance(item, NormalizedItem) for item in items)

    @patch("app.sources.youtube.requests.get")
    def test_item_fields_are_correct(self, mock_get, youtube_config, sample_youtube_feed):
        mock_response = MagicMock()
        mock_response.content = sample_youtube_feed
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = YouTubeFetcher(youtube_config)
        items = fetcher.fetch()

        first_item = items[0]
        assert first_item.source_id == "test_youtube"
        assert first_item.source_display_name == "Test YouTube Channel"
        assert first_item.title == "Test Video Title"
        assert first_item.url == "https://www.youtube.com/watch?v=abc123"
        assert first_item.description == "Test video description"

    @patch("app.sources.youtube.requests.get")
    def test_published_at_is_timezone_aware(self, mock_get, youtube_config, sample_youtube_feed):
        mock_response = MagicMock()
        mock_response.content = sample_youtube_feed
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = YouTubeFetcher(youtube_config)
        items = fetcher.fetch()

        for item in items:
            assert item.published_at.tzinfo is not None

    def test_missing_channel_id_raises_error(self):
        config = SourceConfig(
            id="bad_config",
            type="youtube_channel",
            display_name="Bad Config",
            enabled=True,
            channel_id=None,
        )
        with pytest.raises(ValueError, match="channel_id is required"):
            YouTubeFetcher(config)


class TestGenericRSSFetcher:
    """Tests for generic RSS feed normalization."""

    @pytest.fixture
    def rss_config(self):
        return SourceConfig(
            id="test_rss",
            type="generic_rss",
            display_name="Test RSS Feed",
            enabled=True,
            rss_url="https://example.com/feed.xml",
        )

    @pytest.fixture
    def sample_rss_feed(self):
        """Sample RSS 2.0 feed response."""
        return b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>RSS Item Title</title>
      <link>https://example.com/post/1</link>
      <pubDate>Mon, 15 Jan 2024 10:30:00 GMT</pubDate>
      <description>RSS item description</description>
    </item>
    <item>
      <title>Another RSS Item</title>
      <link>https://example.com/post/2</link>
      <pubDate>Sun, 14 Jan 2024 08:00:00 GMT</pubDate>
      <description>Another RSS description</description>
    </item>
  </channel>
</rss>"""

    @patch("app.sources.generic_rss.requests.get")
    def test_fetch_returns_normalized_items(self, mock_get, rss_config, sample_rss_feed):
        mock_response = MagicMock()
        mock_response.content = sample_rss_feed
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = GenericRSSFetcher(rss_config)
        items = fetcher.fetch()

        assert len(items) == 2
        assert all(isinstance(item, NormalizedItem) for item in items)

    @patch("app.sources.generic_rss.requests.get")
    def test_item_fields_are_correct(self, mock_get, rss_config, sample_rss_feed):
        mock_response = MagicMock()
        mock_response.content = sample_rss_feed
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = GenericRSSFetcher(rss_config)
        items = fetcher.fetch()

        first_item = items[0]
        assert first_item.source_id == "test_rss"
        assert first_item.source_display_name == "Test RSS Feed"
        assert first_item.title == "RSS Item Title"
        assert first_item.url == "https://example.com/post/1"
        assert first_item.description == "RSS item description"

    @patch("app.sources.generic_rss.requests.get")
    def test_published_at_is_timezone_aware(self, mock_get, rss_config, sample_rss_feed):
        mock_response = MagicMock()
        mock_response.content = sample_rss_feed
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = GenericRSSFetcher(rss_config)
        items = fetcher.fetch()

        for item in items:
            assert item.published_at.tzinfo is not None

    def test_missing_rss_url_raises_error(self):
        config = SourceConfig(
            id="bad_config",
            type="generic_rss",
            display_name="Bad Config",
            enabled=True,
            rss_url=None,
        )
        with pytest.raises(ValueError, match="rss_url is required"):
            GenericRSSFetcher(config)
