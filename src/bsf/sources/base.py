from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import Place


class PlaceSource(ABC):
    """A data source that returns businesses for a query in a city."""

    name = "base"

    @abstractmethod
    def search(self, query: str, city: str, limit: int) -> List[Place]:
        ...
