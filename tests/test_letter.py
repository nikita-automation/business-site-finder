import unittest

from bsf.letter import demo_url, qr_svg, reason_text, split_address


class LetterTests(unittest.TestCase):
    def test_split_address(self):
        self.assertEqual(split_address("Fiktivring 37, 45657 Recklinghausen"),
                         ("Fiktivring 37", "45657 Recklinghausen"))

    def test_demo_url(self):
        self.assertEqual(demo_url("https://demo.example.com/", "Schönwerk (fiktiv)"),
                         "https://demo.example.com/schoenwerk")

    def test_qr_is_svg(self):
        self.assertIn("<svg", qr_svg("https://demo.example.com/x"))

    def test_reason(self):
        self.assertIn("keine eigene Website", reason_text("no_site"))
        self.assertIn("zeitgemäß", reason_text("outdated"))


if __name__ == "__main__":
    unittest.main()
