from dataclasses import dataclass
from datetime import datetime


@dataclass
class NormalizedItem:
    source_id: str
    source_display_name: str
    title: str
    url: str
    published_at: datetime
    description: str | None
