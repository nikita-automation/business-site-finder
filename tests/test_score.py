import unittest
from datetime import date

from bsf.audit import Audit, parse_html
from bsf.score import score_place

TODAY = date(2026, 10, 1)


class ScoreTests(unittest.TestCase):
    def test_no_website(self):
        lead = score_place(None, None, TODAY)
        self.assertEqual((lead.site_class, lead.score), ("no_site", 100))

    def test_social_only(self):
        lead = score_place("https://www.facebook.com/x", None, TODAY)
        self.assertEqual(lead.site_class, "no_site")

    def test_unreachable_site(self):
        lead = score_place("http://gone.example", Audit(reachable=False), TODAY)
        self.assertEqual(lead.site_class, "no_site")

    def test_old_site_is_outdated(self):
        audit = Audit(reachable=True, https=False, has_viewport=False,
                      copyright_year=2012, generator="Microsoft FrontPage 4.0")
        lead = score_place("http://old.example", audit, TODAY)
        self.assertEqual(lead.site_class, "outdated")
        self.assertEqual(lead.score, 95)

    def test_modern_site_is_ok(self):
        audit = Audit(reachable=True, https=True, has_viewport=True, copyright_year=2026)
        lead = score_place("https://new.example", audit, TODAY)
        self.assertEqual((lead.site_class, lead.score), ("ok", 0))


class ParseTests(unittest.TestCase):
    def test_parse(self):
        html = ('<meta name="viewport" content="width=device-width">'
                '<meta name="generator" content="Jimdo 2012">&copy; 2010 - 2014 Foo')
        parsed = parse_html(html)
        self.assertTrue(parsed["has_viewport"])
        self.assertEqual(parsed["copyright_year"], 2014)
        self.assertEqual(parsed["generator"], "Jimdo 2012")


if __name__ == "__main__":
    unittest.main()
