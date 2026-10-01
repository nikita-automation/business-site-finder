from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Place:
    """A business found on Google Maps, normalized across data sources."""

    place_id: str
    name: str
    address: str = ""
    city: str = ""
    category: str = ""
    phone: str = ""
    website: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: int = 0
    opening_hours: list = field(default_factory=list)
    source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
