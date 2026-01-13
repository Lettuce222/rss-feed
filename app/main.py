import logging
import sys
from pathlib import Path

from app.config import SourceConfig, load_config
from app.feed_builder import FeedBuilder
from app.models import NormalizedItem
from app.sources.generic_rss import GenericRSSFetcher
from app.sources.youtube import YouTubeFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_fetcher(config: SourceConfig):
    """Create appropriate fetcher based on source type."""
    if config.type == "youtube_channel":
        return YouTubeFetcher(config)
    elif config.type == "generic_rss":
        return GenericRSSFetcher(config)
    else:
        raise ValueError(f"Unknown source type: {config.type}")


def main():
    config_path = Path("config.yaml")
    output_path = Path("docs/feed.xml")

    logger.info(f"Loading config from {config_path}")

    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Filter enabled sources
    enabled_sources = [s for s in config.sources if s.enabled]
    logger.info(f"Processing {len(enabled_sources)} enabled sources...")

    all_items: list[NormalizedItem] = []
    source_urls: dict[str, str] = {}
    success_count = 0
    fail_count = 0

    for source in enabled_sources:
        try:
            fetcher = create_fetcher(source)
            items = fetcher.fetch()
            all_items.extend(items)
            source_urls[source.id] = fetcher.source_url
            logger.info(f"[{source.type}] {source.id}: {len(items)} items fetched")
            success_count += 1
        except Exception as e:
            logger.error(f"[{source.type}] {source.id}: {e}")
            fail_count += 1

    logger.info(
        f"Processing complete: {len(all_items)} items from {success_count} sources "
        f"({fail_count} failed)"
    )

    # If all sources failed, preserve existing feed
    if success_count == 0 and fail_count > 0:
        logger.warning("All sources failed. Preserving existing feed.xml")
        sys.exit(1)

    # Build feed
    builder = FeedBuilder(config.feed)
    feed_xml = builder.build(all_items, source_urls)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write feed
    logger.info(f"Writing feed.xml with {min(len(all_items), config.feed.max_items)} items...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(feed_xml)

    logger.info("Done.")


if __name__ == "__main__":
    main()
