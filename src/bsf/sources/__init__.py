from __future__ import annotations

from .base import PlaceSource


def get_source(name: str) -> PlaceSource:
    if name == "places":
        from .places_source import PlacesSource
        return PlacesSource()
    if name == "sample":
        from .sample_source import SampleSource
        return SampleSource()
    raise ValueError(f"unknown source: {name!r} (use 'places' or 'sample')")
