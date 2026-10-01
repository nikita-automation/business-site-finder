from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"
OUTPUT = ROOT / "output" / "demos"

# Deterministic copy per category: generic offer wording, no claims about the business.
# Each theme: palette, emblem, hero copy, CTA label, optional badge, service tiles.
APPOINTMENT = "Termin vereinbaren"
THEMES = {
    "Friseur": dict(accent="#b0507a", accent2="#e08a6b", emoji="✂️", headline="Ihr Style. Unser Handwerk.",
        sub="Schnitt, Farbe und Pflege mit Zeit für Ihre Wünsche.", cta=APPOINTMENT,
        services_title="Alles für Ihr Haar", services_lead="Von klassisch bis modern.",
        contact_title="Zeit für einen neuen Look?",
        services=[("💇", "Schneiden & Styling", "Damen, Herren und Kinder, individuell beraten."),
                  ("🎨", "Farbe & Strähnen", "Von dezent bis auffällig, schonend umgesetzt."),
                  ("👰", "Festliche Frisuren", "Hochsteckfrisuren für Hochzeit und besondere Anlässe.")]),
    "Barbershop": dict(accent="#1f2a3a", accent2="#5b6b82", emoji="💈", headline="Scharf geschnitten. Sauber rasiert.",
        sub="Haarschnitt und Bartpflege, wie sie sein sollen.", cta=APPOINTMENT,
        services_title="Haar & Bart", services_lead="Klassisches Barber-Handwerk.",
        contact_title="Stuhl frei?",
        services=[("✂️", "Haarschnitt", "Fade, Klassiker oder Undercut."),
                  ("🧔", "Bartpflege", "Formen, Trimmen und Pflege."),
                  ("🪒", "Rasur", "Nassrasur mit heißem Tuch.")]),
    "Nagelstudio": dict(accent="#d1457a", accent2="#f0a0b8", emoji="💅", headline="Schöne Hände. Perfekte Nägel.",
        sub="Pflege und Design für gepflegte Nägel.", cta=APPOINTMENT,
        services_title="Nail Studio", services_lead="Pflege trifft Design.",
        contact_title="Zeit für neue Nägel?",
        services=[("🤲", "Maniküre", "Pflege und Formgebung für Ihre Hände."),
                  ("✨", "Gel-Nägel", "Langlebig und natürlich im Look."),
                  ("🎀", "Nail Art", "Von zart bis ausdrucksstark.")]),
    "Kosmetikstudio": dict(accent="#4f8a6b", accent2="#a8d4b8", emoji="🌿", headline="Zeit für Ihre Haut.",
        sub="Behandlungen, bei denen Sie abschalten können.", cta=APPOINTMENT,
        services_title="Behandlungen", services_lead="Pflege, die guttut.",
        contact_title="Gönnen Sie sich eine Auszeit",
        services=[("🧖", "Gesichtsbehandlung", "Reinigung und Pflege passend zu Ihrem Hauttyp."),
                  ("👁️", "Wimpern & Brauen", "Formen, färben, in Szene setzen."),
                  ("🦶", "Hand- & Fußpflege", "Gepflegt von Kopf bis Fuß.")]),
    "Autowerkstatt": dict(accent="#c2411f", accent2="#f08a3c", emoji="🔧", headline="Ihr Auto in guten Händen.",
        sub="Service, Reparatur und Prüfung für alle gängigen Marken.", cta="Termin buchen",
        services_title="Unsere Leistungen", services_lead="Alles rund ums Fahrzeug.",
        contact_title="Werkstatttermin gesucht?",
        services=[("🛠️", "Inspektion & Wartung", "Regelmäßige Pflege hält Ihr Auto fit."),
                  ("🛞", "Reifenservice", "Wechsel, Einlagerung und Auswuchten."),
                  ("📋", "HU/AU-Vorbereitung", "Wir bereiten Ihr Fahrzeug auf die Prüfung vor.")]),
    "Elektriker": dict(accent="#d99a00", accent2="#f3c94a", emoji="⚡", headline="Strom, sicher installiert.",
        sub="Elektroinstallation und Reparatur aus einer Hand.", cta="Angebot anfragen", badge="Störungsdienst",
        services_title="Elektro-Leistungen", services_lead="Vom Steckdosenwechsel bis zur Neuinstallation.",
        contact_title="Fragen Sie jetzt ein Angebot an",
        services=[("🔌", "Installation & Reparatur", "Neu, Umbau und Instandhaltung."),
                  ("💡", "Beleuchtung", "Planung und Montage für Haus und Betrieb."),
                  ("🚨", "Störungsdienst", "Schnelle Hilfe bei Ausfällen.")]),
    "Klempner": dict(accent="#1f6fae", accent2="#5bb4e0", emoji="💧", headline="Wasser. Wärme. Zuverlässig.",
        sub="Sanitär und Heizung für Haus und Wohnung.", cta="Angebot anfragen", badge="Notdienst",
        services_title="Sanitär & Heizung", services_lead="Wenn es tropft oder kalt bleibt.",
        contact_title="Hilfe bei Rohr und Heizung",
        services=[("🔧", "Rohr- & Leitungsarbeiten", "Reparatur, Austausch und Neuverlegung."),
                  ("🛁", "Badsanierung", "Planung und Umbau aus einer Hand."),
                  ("🔥", "Heizung", "Wartung und Reparatur Ihrer Anlage.")]),
    "Maler": dict(accent="#2e8b8b", accent2="#e0b24a", emoji="🎨", headline="Farbe, die Räume verändert.",
        sub="Anstrich, Tapete und Fassade, sauber ausgeführt.", cta="Angebot anfragen",
        services_title="Malerarbeiten", services_lead="Innen wie außen.",
        contact_title="Neue Farbe gefällig?",
        services=[("🏠", "Innen- & Außenanstrich", "Wände, Decken, Holz und Metall."),
                  ("🖌️", "Tapezieren", "Vom Vlies bis zur Designtapete."),
                  ("🏢", "Fassadenarbeiten", "Schutz und frischer Look fürs Haus.")]),
    "Blumenladen": dict(accent="#4f9a4a", accent2="#e68aa5", emoji="💐", headline="Blumen für jeden Anlass.",
        sub="Frisch gebunden, mit Liebe zum Detail.", cta="Strauß bestellen",
        services_title="Unser Sortiment", services_lead="Für Freude, Feier und Erinnerung.",
        contact_title="Etwas Besonderes gesucht?",
        services=[("🌷", "Sträuße & Gestecke", "Saisonal und individuell gebunden."),
                  ("💒", "Hochzeit & Trauer", "Florale Begleitung zu wichtigen Momenten."),
                  ("🪴", "Pflanzen & Zubehör", "Für Zuhause, Balkon und Garten.")]),
    "Physiotherapie": dict(accent="#2f7f8c", accent2="#7cc8c0", emoji="🧘", headline="Bewegung, die guttut.",
        sub="Therapie und Training für mehr Beweglichkeit.", cta=APPOINTMENT,
        services_title="Therapieangebot", services_lead="Individuell auf Sie abgestimmt.",
        contact_title="Beschwerden? Wir helfen.",
        services=[("🦴", "Krankengymnastik", "Gezielte Übungen bei Beschwerden."),
                  ("🙌", "Manuelle Therapie", "Lösen von Verspannungen und Blockaden."),
                  ("💆", "Massage", "Entspannung und Linderung.")]),
    "Reinigung": dict(accent="#3b6fb0", accent2="#7fb5e8", emoji="👔", headline="Frisch. Sauber. Gepflegt.",
        sub="Textilreinigung und Service rund um Ihre Kleidung.", cta="Abholung anfragen",
        services_title="Unser Service", services_lead="Damit Ihre Kleidung wieder wie neu aussieht.",
        contact_title="Wäsche zu erledigen?",
        services=[("🧺", "Textilreinigung", "Schonend für Kleidung und Stoffe."),
                  ("👕", "Hemdenservice", "Gewaschen und gebügelt."),
                  ("🧵", "Änderungsschneiderei", "Anpassen, kürzen, reparieren.")]),
}
DEFAULT_THEME = dict(accent="#3d5a80", accent2="#8fb3d9", emoji="🏪", headline="Willkommen bei uns.",
    sub="Persönlich, zuverlässig, direkt vor Ort.", cta="Jetzt anrufen",
    services_title="Unsere Leistungen", services_lead="Wir beraten Sie gern.",
    contact_title="Sprechen Sie uns an",
    services=[("🤝", "Beratung", "Persönlich und unverbindlich."),
              ("⭐", "Service", "Zuverlässig und sorgfältig."),
              ("📞", "Termine", "Nach Absprache für Sie da.")])

_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
                          "Ä": "ae", "Ö": "oe", "Ü": "ue"})


def slugify(name: str) -> str:
    name = re.sub(r"\s*\(fiktiv\)", "", name).translate(_UMLAUTS).lower()
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def _env() -> Environment:
    return Environment(loader=FileSystemLoader(str(TEMPLATES)),
                       autoescape=select_autoescape(["html", "j2"]))


def build_demo(place: Mapping, out_dir: Path = OUTPUT) -> Path:
    theme = {"badge": "", **THEMES.get(place["category"], DEFAULT_THEME)}
    html = _env().get_template("site.html.j2").render(
        name=re.sub(r"\s*\(fiktiv\)", "", place["name"]),
        category=place["category"],
        city=place["city"],
        address=place["address"],
        phone=place["phone"],
        rating=place["rating"],
        reviews_count=place["reviews_count"],
        hours=json.loads(place["opening_hours"] or "[]"),
        t=theme,
    )
    target = out_dir / slugify(place["name"]) / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return target
