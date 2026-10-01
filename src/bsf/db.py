from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import Place

SCHEMA = """
CREATE TABLE IF NOT EXISTS places (
    place_id      TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    address       TEXT,
    city          TEXT,
    category      TEXT,
    phone         TEXT,
    website       TEXT,
    rating        REAL,
    reviews_count INTEGER,
    opening_hours TEXT,
    source        TEXT
);
CREATE TABLE IF NOT EXISTS leads (
    place_id   TEXT PRIMARY KEY REFERENCES places(place_id),
    site_class TEXT NOT NULL,
    score      INTEGER NOT NULL,
    reasons    TEXT,
    audit      TEXT
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save_places(conn: sqlite3.Connection, places: Iterable[Place]) -> int:
    """Upsert places; returns the number of rows written."""
    rows = [
        (
            p.place_id, p.name, p.address, p.city, p.category, p.phone,
            p.website, p.rating, p.reviews_count,
            json.dumps(p.opening_hours, ensure_ascii=False), p.source,
        )
        for p in places
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO places VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    conn.commit()
    return len(rows)


def save_lead(conn: sqlite3.Connection, place_id: str, site_class: str,
              score: int, reasons: list, audit: dict | None) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO leads VALUES (?,?,?,?,?)",
        (place_id, site_class, score, json.dumps(reasons, ensure_ascii=False),
         json.dumps(audit) if audit else None),
    )
    conn.commit()
