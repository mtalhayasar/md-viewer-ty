import unittest
from pathlib import Path

from mdviewer.renderer import render, slugify


class RendererTests(unittest.TestCase):
    def test_turkish_slug(self):
        self.assertEqual(slugify("Okumayı Kolaylaştıran Ayrıntılar"), "okumayi-kolaylastiran-ayrintilar")

    def test_toc_and_title(self):
        doc = render("# Başlık\n\n## Bir\n\n## İki\n", Path("."))
        self.assertEqual(doc["title"], "Başlık")
        self.assertEqual([t["level"] for t in doc["toc"]], [1, 2, 2])

    def test_front_matter_title(self):
        doc = render("---\ntitle: Ön Başlık\n---\n# Diğer\n", Path("."))
        self.assertEqual(doc["title"], "Ön Başlık")

    def test_callout(self):
        html = render("> [!WARNING]\n> Dikkat et\n", Path("."))["html"]
        self.assertIn('class="callout callout-warning"', html)
        self.assertIn("Uyarı", html)

    def test_scripts_removed(self):
        html = render('<script>alert(1)</script><img src="x" onerror="alert(1)">\n\n[a](javascript:alert(1))', Path("."))["html"]
        self.assertNotIn("<script", html)
        self.assertNotIn("onerror", html)
        self.assertNotIn('href="javascript:', html)

    def test_code_highlight(self):
        html = render("```python\nx = 1\n```\n", Path("."))["html"]
        self.assertIn('<pre class="code" data-lang="python">', html)

    def test_word_count_ignores_code(self):
        doc = render("bir iki üç\n\n```\nkod kod kod kod\n```\n", Path("."))
        self.assertEqual(doc["words"], 3)


if __name__ == "__main__":
    unittest.main()
