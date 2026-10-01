from __future__ import annotations

import html
import json
import sqlite3
from pathlib import Path

from .demo import OUTPUT as DEMOS, slugify

REPORT = Path(__file__).resolve().parents[2] / "output" / "report.html"
CLASSES = ("no_site", "outdated", "ok")
LABELS = {"no_site": "No website", "outdated": "Outdated website", "ok": "Current website"}


def compute_stats(conn: sqlite3.Connection) -> dict:
    """Aggregate counts from the places and leads tables."""
    total = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
    by_class = {c: 0 for c in CLASSES}
    for row in conn.execute("SELECT site_class, COUNT(*) n FROM leads GROUP BY site_class"):
        by_class[row["site_class"]] = row["n"]
    by_category: dict = {}
    for row in conn.execute(
        """SELECT p.category, l.site_class, COUNT(*) n FROM leads l
           JOIN places p USING (place_id) GROUP BY p.category, l.site_class"""
    ):
        by_category.setdefault(row["category"], {c: 0 for c in CLASSES})[row["site_class"]] = row["n"]
    leads = by_class["no_site"] + by_class["outdated"]
    return {"total": total, "by_class": by_class, "by_category": by_category,
            "leads": leads, "lead_rate": round(100 * leads / total) if total else 0}


def top_leads(conn: sqlite3.Connection, limit: int) -> list:
    return conn.execute(
        """SELECT p.name, p.category, p.address, l.site_class, l.score, l.reasons
           FROM leads l JOIN places p USING (place_id)
           WHERE l.site_class != 'ok' ORDER BY l.score DESC, p.name LIMIT ?""",
        (limit,),
    ).fetchall()


def render(stats: dict, leads: list, demos_dir: Path = DEMOS) -> str:
    e = html.escape
    total = stats["total"] or 1
    seg = "".join(
        f'<div class="seg {c}" style="width:{100 * stats["by_class"][c] / total:.1f}%" '
        f'title="{LABELS[c]}"></div>' for c in CLASSES)
    legend = "".join(
        f'<span><i class="dot {c}"></i>{LABELS[c]}: <b>{stats["by_class"][c]}</b></span>' for c in CLASSES)
    cats = ""
    for cat, counts in sorted(stats["by_category"].items()):
        n = sum(counts.values()) or 1
        bar = "".join(f'<div class="seg {c}" style="width:{100 * counts[c] / n:.1f}%"></div>' for c in CLASSES)
        cats += f'<div class="row"><span>{e(cat)}</span><div class="bar">{bar}</div><b>{n}</b></div>'
    rows = ""
    for r in leads:
        slug = slugify(r["name"])
        demo = f'demos/{slug}/index.html'
        has_demo = (demos_dir / slug / "index.html").exists()
        link = f'<a href="{demo}">demo</a>' if has_demo else "-"
        reasons = "; ".join(json.loads(r["reasons"] or "[]"))
        rows += (f'<tr><td>{e(r["name"])}</td><td>{e(r["category"])}</td>'
                 f'<td><span class="tag {r["site_class"]}">{LABELS[r["site_class"]]}</span></td>'
                 f'<td>{r["score"]}</td><td class="why">{e(reasons)}</td><td>{link}</td></tr>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Pipeline report</title>
<style>
:root{{--bg:#f5f5f7;--card:#fff;--ink:#1d1d1f;--muted:#6e6e73;--line:rgba(0,0,0,.08);
--no_site:#d1457a;--outdated:#e0902f;--ok:#4f9a6b}}
@media(prefers-color-scheme:dark){{:root{{--bg:#000;--card:#1c1c1e;--ink:#f5f5f7;--muted:#a1a1a6;--line:rgba(255,255,255,.12)}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.5}}
main{{max-width:1040px;margin:0 auto;padding:48px 22px 64px}}
h1{{font-size:clamp(30px,5vw,48px);letter-spacing:-.03em;margin:0 0 6px}}p.sub{{color:var(--muted);margin:0 0 32px}}
.cards{{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(min(200px,100%),1fr));margin-bottom:14px}}
.card{{background:var(--card);border-radius:24px;padding:24px 26px}}.card small{{color:var(--muted)}}
.num{{font-size:48px;font-weight:700;letter-spacing:-.04em;line-height:1.1}}
h2{{font-size:22px;letter-spacing:-.02em;margin:0 0 14px}}
.bar{{display:flex;height:14px;border-radius:7px;overflow:hidden;background:var(--line);flex:1}}
.seg.no_site,.dot.no_site{{background:var(--no_site)}}.seg.outdated,.dot.outdated{{background:var(--outdated)}}.seg.ok,.dot.ok{{background:var(--ok)}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}}.legend{{margin-top:12px;font-size:14px;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 18px}}.legend span{{white-space:nowrap}}
.row{{display:grid;grid-template-columns:150px 1fr 30px;gap:12px;align-items:center;padding:6px 0;font-size:15px}}
.table{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--muted);font-weight:500}}
.tag{{padding:2px 10px;border-radius:980px;color:#fff;font-size:12px;white-space:nowrap}}.tag.no_site{{background:var(--no_site)}}.tag.outdated{{background:var(--outdated)}}
.why{{color:var(--muted)}}a{{color:#0071e3}}.gap{{height:14px}}
</style></head><body><main>
<h1>Pipeline report</h1>
<p class="sub">Synthetic sample data, Recklinghausen. No letters were sent.</p>
<div class="cards">
<div class="card"><small>Businesses found</small><div class="num">{stats["total"]}</div></div>
<div class="card"><small>Leads (no site or outdated)</small><div class="num">{stats["leads"]}</div></div>
<div class="card"><small>Lead rate</small><div class="num">{stats["lead_rate"]}%</div></div>
</div>
<div class="card"><h2>Website status</h2><div class="bar">{seg}</div><div class="legend">{legend}</div></div>
<div class="gap"></div>
<div class="card"><h2>By category</h2>{cats}</div>
<div class="gap"></div>
<div class="card table"><h2>Strongest leads</h2><table>
<tr><th>Business</th><th>Category</th><th>Status</th><th>Score</th><th>Why</th><th></th></tr>{rows}</table></div>
</main></body></html>"""


def build_report(conn: sqlite3.Connection, limit: int = 15, out: Path = REPORT) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(compute_stats(conn), top_leads(conn, limit)), encoding="utf-8")
    return out
