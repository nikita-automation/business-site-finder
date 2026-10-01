from __future__ import annotations

import argparse
import os
from pathlib import Path

from . import db
from .audit import audit_site, is_social
from .score import score_place
from .sources import get_source

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "places.db"


def load_env() -> None:
    env = Path(__file__).resolve().parents[2] / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


# Categories where small businesses often have no website (restaurants usually do).
DEFAULT_QUERIES = [
    "Friseur", "Barbershop", "Nagelstudio", "Kosmetikstudio", "Autowerkstatt",
    "Elektriker", "Klempner", "Maler", "Blumenladen", "Physiotherapie",
    "Reinigung",
]


def cmd_collect(args: argparse.Namespace) -> None:
    source = get_source(args.source)
    queries = args.query or DEFAULT_QUERIES
    conn = db.connect(DB_PATH)
    total = 0
    for query in queries:
        places = source.search(query, args.city, args.limit)
        total += db.save_places(conn, places)  # place_id is the key: duplicates merge
        print(f"[{source.name}] {query}: {len(places)} places")
    unique = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
    print(f"saved {total} rows, {unique} unique places in {args.city}")


def cmd_analyze(args: argparse.Namespace) -> None:
    conn = db.connect(DB_PATH)
    counts: dict = {}
    for row in conn.execute("SELECT place_id, website FROM places").fetchall():
        website = row["website"]
        audit = None
        if website and not is_social(website):
            audit = audit_site(website, live=args.live)
        lead = score_place(website, audit)
        db.save_lead(conn, row["place_id"], lead.site_class, lead.score, lead.reasons,
                     audit.to_dict() if audit else None)
        counts[lead.site_class] = counts.get(lead.site_class, 0) + 1
    print("analyzed:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


def cmd_leads(args: argparse.Namespace) -> None:
    conn = db.connect(DB_PATH)
    rows = conn.execute(
        """SELECT p.name, p.category, l.site_class, l.score, l.reasons
           FROM leads l JOIN places p USING (place_id)
           WHERE l.site_class != 'ok' ORDER BY l.score DESC, p.name LIMIT ?""",
        (args.top,),
    ).fetchall()
    for r in rows:
        print(f"{r['score']:>3}  {r['site_class']:<9} {r['name']:<32} {r['category']:<15} {r['reasons']}")


def cmd_demo(args: argparse.Namespace) -> None:
    from .demo import build_demo, OUTPUT, slugify  # needs jinja2

    conn = db.connect(DB_PATH)
    rows = conn.execute(
        """SELECT p.*, l.site_class, l.score FROM leads l JOIN places p USING (place_id)
           WHERE l.site_class != 'ok' ORDER BY l.score DESC, p.name LIMIT ?""",
        (args.top,),
    ).fetchall()
    for row in rows:
        build_demo(row)
    index = "\n".join(
        f'<li><a href="{slugify(r["name"])}/index.html">{r["name"]}</a> '
        f'({r["category"]}, {r["site_class"]}, score {r["score"]})</li>'
        for r in rows
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "index.html").write_text(
        f'<!doctype html><meta charset="utf-8"><title>Demo sites</title>'
        f'<h1>Demo sites</h1><ul>{index}</ul>', encoding="utf-8")
    print(f"built {len(rows)} demo sites in {OUTPUT}")


def cmd_letter(args: argparse.Namespace) -> None:
    from .letter import build_letter, LETTERS  # needs jinja2, qrcode, Chrome

    conn = db.connect(DB_PATH)
    rows = conn.execute(
        """SELECT p.*, l.site_class, l.score FROM leads l JOIN places p USING (place_id)
           WHERE l.site_class != 'ok' ORDER BY l.score DESC, p.name LIMIT ?""",
        (args.top,),
    ).fetchall()
    for row in rows:
        build_letter(row, row["site_class"])
    print(f"built {len(rows)} letters in {LETTERS}")


def cmd_report(args: argparse.Namespace) -> None:
    from .report import build_report

    print(f"report: {build_report(db.connect(DB_PATH), args.top)}")


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(prog="bsf")
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="fetch businesses into SQLite")
    collect.add_argument("--source", default="sample", choices=["sample", "places"])
    collect.add_argument("--query", action="append", help="repeatable; default: built-in category list")
    collect.add_argument("--city", default="Recklinghausen")
    collect.add_argument("--limit", type=int, default=60, help="per query, max 60")
    collect.set_defaults(func=cmd_collect)

    analyze = sub.add_parser("analyze", help="audit websites and score each business")
    analyze.add_argument("--live", action="store_true", help="fetch real sites instead of fixtures")
    analyze.set_defaults(func=cmd_analyze)

    leads = sub.add_parser("leads", help="show the strongest leads")
    leads.add_argument("--top", type=int, default=15)
    leads.set_defaults(func=cmd_leads)

    demo = sub.add_parser("demo", help="render a demo site for the top leads")
    demo.add_argument("--top", type=int, default=10)
    demo.set_defaults(func=cmd_demo)

    letter = sub.add_parser("letter", help="build print-ready PDF letters for the top leads")
    letter.add_argument("--top", type=int, default=10)
    letter.set_defaults(func=cmd_letter)

    report = sub.add_parser("report", help="build an HTML summary of the pipeline run")
    report.add_argument("--top", type=int, default=15)
    report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
