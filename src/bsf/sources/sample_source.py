from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..models import Place
from .base import PlaceSource

SAMPLE = Path(__file__).resolve().parents[3] / "data" / "sample" / "places.json"


class SampleSource(PlaceSource):
    """Synthetic, fictional businesses. Lets the pipeline run with no API key."""

    name = "sample"

    def search(self, query: str, city: str, limit: int) -> List[Place]:
        items = json.loads(SAMPLE.read_text(encoding="utf-8"))
        matching = [i for i in items if i["category"].lower() == query.lower()]
        items = matching or items  # unknown category: fall back to everything
        return [Place(**{**item, "source": "sample"}) for item in items[:limit]]
