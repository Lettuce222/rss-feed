from datetime import UTC, datetime

import feedparser
import requests

from app.config import SourceConfig
from app.models import NormalizedItem

from .base import SourceFetcher


class YouTubeFetcher(SourceFetcher):
    """Fetcher for YouTube channels using the official RSS feed."""

    YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    TIMEOUT = 30

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        if not config.channel_id:
            raise ValueError(f"channel_id is required for youtube_channel source: {config.id}")

    def fetch(self) -> list[NormalizedItem]:
        """Fetch videos from YouTube channel RSS feed."""
        url = self.YOUTUBE_RSS_URL.format(channel_id=self.config.channel_id)
        response = requests.get(url, timeout=self.TIMEOUT)
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        items = []

        for entry in feed.entries:
            published_at = self._parse_date(entry.get("published"))
            if published_at is None:
                continue

            item = NormalizedItem(
                source_id=self.source_id,
                source_display_name=self.display_name,
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                published_at=published_at,
                description=entry.get("summary"),
            )
            items.append(item)

        return items

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to timezone-aware datetime."""
        if not date_str:
            return None
        try:
            # feedparser provides parsed time in time_struct format
            # but we have the raw string, so parse it
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except (ValueError, TypeError):
            return None

    @property
    def source_url(self) -> str:
        """Return the source URL for RSS <source> element."""
        return self.YOUTUBE_RSS_URL.format(channel_id=self.config.channel_id)
