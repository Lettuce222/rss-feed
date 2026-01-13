from abc import ABC, abstractmethod

from app.config import SourceConfig
from app.models import NormalizedItem


class SourceFetcher(ABC):
    """Base class for source fetchers."""

    def __init__(self, config: SourceConfig):
        self.config = config

    @abstractmethod
    def fetch(self) -> list[NormalizedItem]:
        """Fetch items from the source and return normalized items."""
        pass

    @property
    def source_id(self) -> str:
        return self.config.id

    @property
    def display_name(self) -> str:
        return self.config.display_name
