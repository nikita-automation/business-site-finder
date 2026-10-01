from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Mapping, Optional

import qrcode
import qrcode.image.svg
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .demo import OUTPUT as DEMOS, TEMPLATES, build_demo, slugify

ROOT = Path(__file__).resolve().parents[2]
LETTERS = ROOT / "output" / "letters"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def load_sender() -> dict:
    for name in ("sender.json", "sender.example.json"):
        path = ROOT / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("sender.json or sender.example.json missing")


def demo_url(base: str, place_name: str) -> str:
    return f"{base.rstrip('/')}/{slugify(place_name)}"


def qr_svg(url: str) -> str:
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=0)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode()


def split_address(address: str) -> tuple[str, str]:
    parts = [p.strip() for p in address.split(",")]
    return parts[0], ", ".join(parts[1:])


def reason_text(site_class: str) -> str:
    if site_class == "no_site":
        return "Sie bislang keine eigene Website haben"
    return "Ihre aktuelle Website nicht mehr ganz zeitgemäß wirkt (zum Beispiel auf dem Smartphone)"


def _chrome(*args: str) -> None:
    if not Path(CHROME).exists():
        raise RuntimeError("Google Chrome not found; needed for screenshots and PDF")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", *args],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)


def screenshot_data_uri(page: Path) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "shot.png"
        _chrome(f"--screenshot={png}", "--window-size=1280,860", "--force-device-scale-factor=1", "--blink-settings=preferredColorScheme=0", page.resolve().as_uri())
        return "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()


def build_letter(place: Mapping, site_class: str, sender: Optional[dict] = None,
                 out_dir: Path = LETTERS, demos_dir: Path = DEMOS) -> Path:
    s = sender or load_sender()
    page = build_demo(place, demos_dir)
    street, zip_city = split_address(place["address"])
    url = demo_url(s["demo_base_url"], place["name"])
    html = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                       autoescape=select_autoescape(["html", "j2"])).get_template("letter.html.j2").render(
        s=s, name=place["name"].replace(" (fiktiv)", ""), category=place["category"], city=place["city"],
        street=street, zip_city=zip_city, reason=reason_text(site_class),
        screenshot=screenshot_data_uri(page), qr_svg=qr_svg(url), url=url,
        date=date.today().strftime("%d.%m.%Y"),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(place["name"])
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "letter.html"
        src.write_text(html, encoding="utf-8")
        pdf = out_dir / f"{slug}.pdf"
        _chrome(f"--print-to-pdf={pdf}", "--no-pdf-header-footer", src.as_uri())
    return pdf
