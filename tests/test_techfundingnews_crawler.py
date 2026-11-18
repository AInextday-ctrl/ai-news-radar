#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.techfundingnews_crawler import crawl_techfundingnews, is_techfundingnews_url


SAMPLE_TFN_HTML = """<!doctype html>
<html>
<head>
  <meta property="og:title" content="Sumary lands $25M seed led by Singular — TFN" />
  <meta property="og:image" content="https://techfundingnews.com/wp-content/uploads/2026/11/Sumary-co-founders.png" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Article",
        "headline": "Sumary lands $25M seed led by Singular as AI accounting race heats up",
        "datePublished": "2026-11-10T10:53:48+00:00",
        "author": [{"@id": "https://techfundingnews.com/#/schema/person/abc123"}]
      },
      {
        "@type": "Person",
        "@id": "https://techfundingnews.com/#/schema/person/abc123",
        "name": "Sofia Chesnokova"
      }
    ]
  }
  </script>
</head>
<body>
  <article>
    <div class="entry-content">
      <ul class="wp-block-list">
        <li>Leading bullet summary that duplicates the executive summary above the article.</li>
      </ul>
      <p>Copenhagen-based Sumary, which develops AI software for accounting firms, has raised $25 million in a seed round led by Singular.</p>
      <h2 class="wp-block-heading">Sell to firms or become one</h2>
      <p>Since July, the AI accounting space has split between startups selling software to established firms and startups operating as accounting firms in their own right.</p>
      <p>Sumary says it will work with any ledger the accountant currently uses and aims to become the firm's operating system across Nordic markets and London.</p>
    </div>
  </article>
</body>
</html>
"""


class TestTechFundingNewsCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_techfundingnews_url("https://techfundingnews.com/sumary-25m-seed-ai-accounting-firms/"))
        self.assertFalse(is_techfundingnews_url("https://nypost.com/2026/11/16/us-news/trump"))

    def test_yoast_person_id_and_leading_bullets_strip(self):
        res = crawl_techfundingnews(
            "https://techfundingnews.com/sumary-25m-seed-ai-accounting-firms/",
            html_text=SAMPLE_TFN_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Sofia Chesnokova")
        self.assertIn("### Sell to firms or become one", res["full_text"])
        self.assertNotIn("Leading bullet summary", res["full_text"])
        self.assertEqual(res["published_at"], "2026-11-10T10:53:48+00:00")


if __name__ == "__main__":
    unittest.main()
