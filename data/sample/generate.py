"""Generate synthetic businesses for demo/testing. All names are fictional."""
from __future__ import annotations
import json
import random
from pathlib import Path

random.seed(42)

CATEGORIES = {
    "Friseur": ["Haarwerk", "Schnittpunkt", "Kamm & Schere", "Locke", "Haarlinie", "Spitzenschnitt"],
    "Barbershop": ["Fade Corner", "Bartwerk", "Klingenschmiede", "Cut Club"],
    "Nagelstudio": ["Nagelzauber", "Glanzfinger", "Nail Atelier", "Lackiert"],
    "Kosmetikstudio": ["Hautnah", "Schönwerk", "Glow Studio", "Reinhaut"],
    "Autowerkstatt": ["Schraubers Eck", "Motorwerk", "Radlager", "Zündfunke", "Kfz Meisterblick"],
    "Elektriker": ["Stromkreis", "Voltwerk", "Leitung Plus", "Funkenflug"],
    "Klempner": ["Rohrmeister", "Dichtung & Co", "Wasserwerk Klein", "Hahn & Sohn"],
    "Maler": ["Pinselstrich", "Farbwerk", "Wandkunst", "Rollenspiel", "Tapetenwechsel"],
    "Blumenladen": ["Blütenzauber", "Floristik Stiel", "Grüne Ecke", "Rosenzeit", "Tulpenfeld"],
    "Physiotherapie": ["Bewegungsraum", "Gelenkig", "Physio Mitte", "Rücken frei"],
    "Reinigung": ["Sauberkeit Pur", "Fleckenfrei", "Textilpflege Rein", "Blitzblank", "Staubfrei"],
}
STREETS = ["Musterstraße", "Beispielweg", "Probeallee", "Testplatz", "Demogasse",
           "Fiktivring", "Beispielmarkt", "Probestraße"]
HOURS = [["Mo-Fr 09:00-18:00", "Sa 09:00-13:00"], ["Di-Sa 10:00-18:00"],
         ["Mo-Fr 08:00-17:00"], ["Mo-Sa 09:00-19:00"]]


def website(slug: str) -> str | None:
    roll = random.random()
    if roll < 0.35:
        return None
    if roll < 0.50:
        return f"https://www.facebook.com/{slug}-fiktiv"
    if roll < 0.75:
        return f"http://{slug}.example"
    return f"https://www.{slug}.example"


places = []
n = 0
for category, names in CATEGORIES.items():
    for name in names:
        n += 1
        if n > 50:
            break
        slug = name.lower().replace(" & ", "-").replace(" ", "-")
        places.append({
            "place_id": f"sample-{n:03d}",
            "name": f"{name} (fiktiv)",
            "address": f"{random.choice(STREETS)} {random.randint(1, 60)}, 45657 Recklinghausen",
            "city": "Recklinghausen",
            "category": category,
            "phone": f"+49 2361 {900000 + n:06d}",
            "website": website(slug),
            "rating": round(random.uniform(3.6, 4.9), 1),
            "reviews_count": random.randint(4, 260),
            "opening_hours": random.choice(HOURS),
        })

out = Path(__file__).with_name("places.json")
out.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {len(places)} places")


# --- Site fixtures: offline HTML so the audit stage runs without network access ---
from urllib.parse import urlparse

SOCIAL = ("facebook.com", "instagram.com")
MODERN = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title></head><body><h1>{name}</h1><p>Willkommen!</p>
<footer>&copy; 2026 {name}</footer></body></html>
"""
OLD = """<html><head><title>{name}</title>
<meta name="generator" content="{gen}"></head>
<body bgcolor="#cccccc"><table width="800"><tr><td><h1>{name}</h1>
<p>Herzlich willkommen auf unserer Homepage!</p></td></tr></table>
<p>Copyright {year} {name}</p></body></html>
"""
fx = random.Random(7)  # separate RNG: keeps places.json identical
sites = Path(__file__).with_name("sites")
sites.mkdir(exist_ok=True)
for old_file in sites.glob("*.html"):
    old_file.unlink()
count = 0
for p in places:
    url = p["website"]
    if not url or any(s in url for s in SOCIAL):
        continue
    parsed = urlparse(url)
    is_old = parsed.scheme == "http" or fx.random() < 0.2
    name = p["name"].replace(" (fiktiv)", "")
    html = (OLD.format(name=name, year=fx.randint(2009, 2018),
                       gen=fx.choice(["Microsoft FrontPage 4.0", "Jimdo 2012", "Dreamweaver 8"]))
            if is_old else MODERN.format(name=name))
    (sites / f"{parsed.netloc}.html").write_text(html, encoding="utf-8")
    count += 1
print(f"wrote {count} site fixtures")
