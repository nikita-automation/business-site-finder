import json
import tempfile
import unittest
from pathlib import Path

from bsf.demo import build_demo, slugify

PLACE = {
    "name": "Schönwerk (fiktiv)", "category": "Kosmetikstudio", "city": "Recklinghausen",
    "address": "Musterstraße 1", "phone": "+49 2361 900001", "rating": 4.4,
    "reviews_count": 12, "opening_hours": json.dumps(["Mo-Fr 09:00-18:00"]),
}


class DemoTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Schönwerk (fiktiv)"), "schoenwerk")
        self.assertEqual(slugify("Kamm & Schere (fiktiv)"), "kamm-schere")

    def test_build_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = build_demo(PLACE, Path(tmp))
            html = path.read_text(encoding="utf-8")
        self.assertIn("Schönwerk", html)
        self.assertIn("Mo-Fr 09:00-18:00", html)
        self.assertIn("nicht online veröffentlicht", html)

    def test_escapes_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = build_demo({**PLACE, "name": "<script>x</script>"}, Path(tmp)).read_text(encoding="utf-8")
        self.assertNotIn("<script>x</script>", html)


if __name__ == "__main__":
    unittest.main()
