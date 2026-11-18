#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.semafor_crawler import is_semafor_url, crawl_semafor


class TestSemaforCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_semafor_url("https://www.semafor.com/article/11/17/2026/some-nvidia-directors-push"))
        self.assertFalse(is_semafor_url("https://siliconangle.com/2026/11/17/lancedb/"))

    def test_jsonld_authors_eyebrow_strip_and_avatar_cover_dedup(self):
        html_doc = """
        <html>
        <head>
          <meta property="og:image" content="https://img.semafor.com/ed7879de-2940x1960.jpg?rect=0,208,2940,1544&amp;w=1200&amp;h=630" />
          <script type="application/ld+json">
          {
            "@type": "NewsArticle",
            "headline": "Exclusive / Some Nvidia directors continue push to bring Huang back",
            "datePublished": "2026-11-18T02:06:48Z",
            "author": [
              {"@type": "Person", "name": "Reed Albergotti"},
              {"@type": "Person", "name": "Rohan Goswami"}
            ]
          }
          </script>
        </head>
        <body>
          <main>
            <h1>Exclusive / Some Nvidia directors continue push to bring Huang back</h1>
            <figure><img src="https://img.semafor.com/e2e40401-512x512.png?h=125&amp;w=125&amp;auto=format" alt="Author" /></figure>
            <figure><img src="https://img.semafor.com/ed7879de-2940x1960.jpg?w=740&amp;q=75" /><figcaption>Mike Blake/Reuters</figcaption></figure>
            <p>Despite Nvidia’s proclamation Tuesday that it did not plan to bring ousted CEO Jensen Huang back to the chipmaker, at least three directors continue to argue internally for his return.</p>
            <h3>Know More</h3>
            <p>Huang has met with several technology executives and spoken with at least one board member in recent days as Nvidia narrows its external CEO search across semiconductor leaders including ARM and Marvell.</p>
            <p>Board chairman Harvey Jones reiterated on the earnings call that the company remains focused on its formal succession search while cooperating with ongoing federal compliance reviews.</p>
          </main>
        </body>
        </html>
        """
        res = crawl_semafor(
            "https://www.semafor.com/article/11/17/2026/some-nvidia-directors-push",
            html_text=html_doc,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Some Nvidia directors continue push to bring Huang back")
        self.assertEqual(res["author"], "Reed Albergotti and Rohan Goswami")
        self.assertIn("### Know More", res["paragraphs"])
        # Both 125x125 author avatar AND duplicate cover image stripped from inline_images
        self.assertEqual(len(res["inline_images"]), 0)


if __name__ == "__main__":
    unittest.main()
