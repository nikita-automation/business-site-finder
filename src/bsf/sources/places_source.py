from __future__ import annotations

import json
import os
import urllib.request
from typing import List

from ..models import Place
from .base import PlaceSource

URL = "https://places.googleapis.com/v1/places:searchText"
PAGE_SIZE = 20  # API maximum per page; at most 3 pages (60 results) per query
FIELDS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress",
    "places.primaryTypeDisplayName", "places.internationalPhoneNumber",
    "places.websiteUri", "places.rating", "places.userRatingCount",
    "places.regularOpeningHours.weekdayDescriptions", "places.businessStatus",
    "nextPageToken",
])


class PlacesSource(PlaceSource):
    """Official Google Places API (New), Text Search."""

    name = "places"

    def __init__(self, api_key: str | None = None, timeout: int = 60):
        self.api_key = api_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")
        self.timeout = timeout
        if not self.api_key:
            raise RuntimeError("GOOGLE_PLACES_API_KEY is not set (see .env.example)")

    def search(self, query: str, city: str, limit: int) -> List[Place]:
        places: List[Place] = []
        token = None
        while len(places) < limit:
            body = {
                "textQuery": f"{query} in {city}",
                "languageCode": "de",
                "regionCode": "DE",
                "pageSize": min(PAGE_SIZE, limit - len(places)),
            }
            if token:
                body["pageToken"] = token
            data = self._post(body)
            for item in data.get("places", []):
                if item.get("businessStatus", "OPERATIONAL") != "OPERATIONAL":
                    continue
                places.append(self._to_place(item, city))
            token = data.get("nextPageToken")
            if not token:
                break
        return places[:limit]

    def _post(self, body: dict) -> dict:
        req = urllib.request.Request(
            URL,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": FIELDS,
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.load(resp)

    @staticmethod
    def _to_place(item: dict, city: str) -> Place:
        hours = item.get("regularOpeningHours", {}).get("weekdayDescriptions", [])
        return Place(
            place_id=item["id"],
            name=item.get("displayName", {}).get("text", ""),
            address=item.get("formattedAddress", ""),
            city=city,
            category=item.get("primaryTypeDisplayName", {}).get("text", ""),
            phone=item.get("internationalPhoneNumber", ""),
            website=item.get("websiteUri") or None,
            rating=item.get("rating"),
            reviews_count=item.get("userRatingCount", 0),
            opening_hours=hours,
            source="places",
        )
