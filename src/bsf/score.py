from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from .audit import Audit, is_social

OLD_GENERATORS = ("frontpage", "dreamweaver", "jimdo", "homepage-baukasten")
OUTDATED_THRESHOLD = 40


@dataclass
class Lead:
    site_class: str  # no_site | outdated | ok
    score: int       # 0-100, higher = stronger case for a new site
    reasons: List[str] = field(default_factory=list)


def score_place(website: Optional[str], audit: Optional[Audit], today: Optional[date] = None) -> Lead:
    year = (today or date.today()).year

    if not website:
        return Lead("no_site", 100, ["no website listed"])
    if is_social(website):
        return Lead("no_site", 90, ["only a social media page, no own website"])
    if audit is None or not audit.reachable:
        return Lead("no_site", 80, ["website listed but not reachable"])

    points, reasons = 0, []
    if not audit.https:
        points += 25
        reasons.append("no HTTPS")
    if not audit.has_viewport:
        points += 30
        reasons.append("not mobile-friendly (no viewport)")
    if audit.copyright_year is not None:
        age = year - audit.copyright_year
        if age >= 5:
            points += 25
            reasons.append(f"copyright year {audit.copyright_year} ({age} years old)")
        elif age >= 3:
            points += 12
            reasons.append(f"copyright year {audit.copyright_year}")
    if any(g in audit.generator.lower() for g in OLD_GENERATORS):
        points += 15
        reasons.append(f"legacy site builder: {audit.generator}")

    points = min(points, 100)
    site_class = "outdated" if points >= OUTDATED_THRESHOLD else "ok"
    return Lead(site_class, points, reasons or ["site looks current"])
