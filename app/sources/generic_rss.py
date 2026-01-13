import time
from datetime import UTC, datetime

import feedparser
import requests

from app.config import SourceConfig
from app.models import NormalizedItem

from .base import SourceFetcher


class GenericRSSFetcher(SourceFetcher):
    """Fetcher for generic RSS/Atom feeds."""

    TIMEOUT = 30

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        if not config.rss_url:
            raise ValueError(f"rss_url is required for generic_rss source: {config.id}")

    def fetch(self) -> list[NormalizedItem]:
        """Fetch items from a generic RSS/Atom feed."""
        response = requests.get(self.config.rss_url, timeout=self.TIMEOUT)
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        items = []

        for entry in feed.entries:
            published_at = self._parse_date(entry)
            if published_at is None:
                continue

            description = entry.get("summary") or entry.get("description")

            item = NormalizedItem(
                source_id=self.source_id,
                source_display_name=self.display_name,
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                published_at=published_at,
                description=description,
            )
            items.append(item)

        return items

    def _parse_date(self, entry) -> datetime | None:
        """Parse date from feedparser entry."""
        # feedparser provides parsed_time as time.struct_time
        time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if time_struct:
            timestamp = time.mktime(time_struct)
            return datetime.fromtimestamp(timestamp, tz=UTC)

        # Fallback to string parsing
        date_str = entry.get("published") or entry.get("updated")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except (ValueError, TypeError):
                pass

        return None

    @property
    def source_url(self) -> str:
        """Return the source URL for RSS <source> element."""
        return self.config.rss_url
