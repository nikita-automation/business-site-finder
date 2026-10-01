from __future__ import annotations

import re
import time
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

SOCIAL_HOSTS = ("facebook.com", "instagram.com", "linktr.ee", "tiktok.com")
FIXTURES = Path(__file__).resolve().parents[2] / "data" / "sample" / "sites"

_VIEWPORT = re.compile(r"<meta[^>]+name=[\"']viewport[\"']", re.I)
_GENERATOR = re.compile(r"<meta[^>]+name=[\"']generator[\"'][^>]+content=[\"']([^\"']+)", re.I)
_COPYRIGHT = re.compile(
    r"(?:©|&copy;|copyright)\s*(?:\(c\)\s*)?(?:\d{4}\s*[-–]\s*)?(\d{4})", re.I
)


@dataclass
class Audit:
    reachable: bool = False
    https: bool = False
    has_viewport: bool = False
    copyright_year: Optional[int] = None
    generator: str = ""
    response_ms: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


def is_social(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == h or host.endswith("." + h) for h in SOCIAL_HOSTS)


def parse_html(html: str) -> dict:
    years = [int(y) for y in _COPYRIGHT.findall(html)]
    gen = _GENERATOR.search(html)
    return {
        "has_viewport": bool(_VIEWPORT.search(html)),
        "copyright_year": max(years) if years else None,
        "generator": gen.group(1).strip() if gen else "",
    }


def fetch_live(url: str, timeout: int = 15) -> tuple[Optional[str], Optional[int]]:
    started = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "business-site-finder/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read(500_000).decode("utf-8", errors="replace")
    except Exception:
        return None, None
    return html, int((time.monotonic() - started) * 1000)


def fetch_fixture(url: str) -> tuple[Optional[str], Optional[int]]:
    path = FIXTURES / f"{urlparse(url).netloc}.html"
    if not path.exists():
        return None, None
    return path.read_text(encoding="utf-8"), None


def audit_site(url: str, live: bool = False) -> Audit:
    html, ms = (fetch_live if live else fetch_fixture)(url)
    audit = Audit(https=urlparse(url).scheme == "https", response_ms=ms)
    if html is None:
        return audit
    audit.reachable = True
    for key, value in parse_html(html).items():
        setattr(audit, key, value)
    return audit
