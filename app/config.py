from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml


@dataclass
class FeedConfig:
    title: str
    description: str
    link: str
    language: str
    max_items: int


@dataclass
class SourceConfig:
    id: str
    type: Literal["youtube_channel", "generic_rss"]
    display_name: str
    enabled: bool
    channel_id: str | None = None
    rss_url: str | None = None


@dataclass
class AppConfig:
    feed: FeedConfig
    sources: list[SourceConfig]


def load_config(config_path: Path = Path("config.yaml")) -> AppConfig:
    """Load configuration from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(
            f"Error: {config_path} not found.\n"
            "Please copy config.example.yaml to config.yaml and edit it."
        )

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    feed_data = data["feed"]
    feed_config = FeedConfig(
        title=feed_data["title"],
        description=feed_data["description"],
        link=feed_data["link"],
        language=feed_data["language"],
        max_items=feed_data.get("max_items", 100),
    )

    sources = []
    for source_data in data.get("sources", []):
        source = SourceConfig(
            id=source_data["id"],
            type=source_data["type"],
            display_name=source_data["display_name"],
            enabled=source_data.get("enabled", True),
            channel_id=source_data.get("channel_id"),
            rss_url=source_data.get("rss_url"),
        )
        sources.append(source)

    return AppConfig(feed=feed_config, sources=sources)
