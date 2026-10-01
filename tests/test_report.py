import unittest

from bsf import db
from bsf.models import Place
from bsf.report import compute_stats, render, top_leads


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.save_places(self.conn, [
            Place("a", "A <b>", category="Friseur"),
            Place("b", "B", category="Friseur"),
            Place("c", "C", category="Maler"),
        ])
        db.save_lead(self.conn, "a", "no_site", 100, ["no website listed"], None)
        db.save_lead(self.conn, "b", "outdated", 60, ["no HTTPS"], None)
        db.save_lead(self.conn, "c", "ok", 0, ["site looks current"], None)

    def test_stats(self):
        stats = compute_stats(self.conn)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["leads"], 2)
        self.assertEqual(stats["lead_rate"], 67)
        self.assertEqual(stats["by_category"]["Friseur"]["outdated"], 1)

    def test_render_escapes_and_orders(self):
        leads = top_leads(self.conn, 10)
        self.assertEqual([r["name"] for r in leads], ["A <b>", "B"])
        out = render(compute_stats(self.conn), leads)
        self.assertNotIn("A <b>", out)
        self.assertIn("A &lt;b&gt;", out)


if __name__ == "__main__":
    unittest.main()
