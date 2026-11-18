#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for The Washington Post (`crawlers/wapo_crawler.py`) and
The Washington Sun (`crawlers/washsun_crawler.py`) isolated crawlers.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.wapo_crawler import (
    crawl_wapo,
    is_wapo_url,
    _is_valid_wapo_image,
    _wrap_wapo_imrs,
)
from crawlers.washsun_crawler import (
    crawl_washsun,
    is_washsun_url,
    _is_valid_washsun_image,
)
from article_extractor import ArticleExtractor


SAMPLE_WAPO_HTML = """<!DOCTYPE html>
<html>
<head><title>Nvidia scandal hits Trump’s political vulnerabilities - The Washington Post</title></head>
<body>
<script id="__NEXT_DATA__" type="application/json">{
  "props": {
    "pageProps": {
      "globalContent": {
        "headlines": {"basic": "Nvidia scandal hits Trump’s political vulnerabilities after Democratic sweep"},
        "first_publish_date": "2026-11-14T10:00:00.000Z",
        "credits": {"by": [{"name": "Isaac Arnsdorf"}, {"name": "Cat Zakrzewski"}]},
        "promo_items": {
          "basic": {
            "type": "image",
            "url": "https://cloudfront-us-east-1.images.arcpublishing.com/wapo/OJGBA6V7NXPZ6V6G4P2TBNAM6I.JPG"
          }
        },
        "content_elements": [
          {"type": "text", "content": "Sex. Money. Power. Espionage. As Washington scandals go, this one has everything and connects directly to voter anxieties about artificial intelligence."},
          {"type": "header", "content": "Political fallout on Capitol Hill"},
          {"type": "text", "content": "Lawmakers from both parties signaled new scrutiny over chip export controls and data center subsidies following the disclosures this week."},
          {"type": "text", "content": "White House officials sought to distance the administration from the controversy while emphasizing domestic semiconductor manufacturing goals."},
          {"type": "text", "content": "Most Read From The Washington Post"}
        ]
      }
    }
  }
}</script>
</body>
</html>
"""

SAMPLE_WASHSUN_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="Bank CEOs, NSA Tell Congress That AI-Driven Patches Are Behind Outages - The Washington Sun" />
  <meta property="og:image" content="https://static.washingtonsun.com/dims4/default/ee03c91/resize/1440x810!/ap25064000941559.jpg" />
  <script type="application/ld+json">
    {"@type": "Article", "headline": "Bank CEOs, NSA Tell Congress That AI-Driven Patches Are Behind Outages", "datePublished": "2026-11-18T00:45:56Z", "author": [{"@type": "Person", "name": "Jeff Stein", "image": {"url": "https://static.washingtonsun.com/staff-jeff-stein-mug-500px.png"}}]}
  </script>
</head>
<body>
  <h1>Bank CEOs, NSA Tell Congress That AI-Driven Patches Are Behind Outages</h1>
  <div class="RichTextArticleBody">
    <p>Wall Street executives and the National Security Agency told lawmakers that automated AI code patches triggered major infrastructure outages across financial clearing networks.</p>
    <figure><img src="https://static.washingtonsun.com/staff-jeff-stein-mug-500px.png" alt="Jeff Stein" /></figure>
    <p>Chief technology officers from four major U.S. banks said rapid deployment of unverified model-generated hotfixes overwhelmed fallback routing hardware during peak trading hours.</p>
    <p>Congressional committees requested full post-mortem logs from banking regulators and federal cybersecurity agencies by the end of the week.</p>
    <p>Sign up for The Washington Sun daily briefing.</p>
  </div>
</body>
</html>
"""


class TestWashingtonCrawlers(unittest.TestCase):
    def test_url_and_image_guards(self):
        self.assertTrue(is_wapo_url("https://www.washingtonpost.com/politics/2026/11/14/test/?pwapi_token=abc"))
        self.assertFalse(is_wapo_url("https://www.nytimes.com/2026/11/17/test.html"))
        self.assertTrue(_is_valid_wapo_image("https://cloudfront-us-east-1.images.arcpublishing.com/wapo/ABC.JPG"))
        self.assertFalse(_is_valid_wapo_image("https://img-s-msn-com.akamaized.net/tenant/amp/entityid/AA2024Mm.img"))
        self.assertIn("wp-apps/imrs.php?src=", _wrap_wapo_imrs("https://cloudfront-us-east-1.images.arcpublishing.com/wapo/ABC.JPG"))

        self.assertTrue(is_washsun_url("https://www.washingtonsun.com/technology/bank-ceos-nsa"))
        self.assertFalse(is_washsun_url("https://www.washingtonpost.com/technology/test"))
        self.assertFalse(_is_valid_washsun_image("https://static.washingtonsun.com/staff-jeff-stein-mug-500px.png"))

    def test_wapo_next_data_and_routing(self):
        url = "https://www.washingtonpost.com/politics/2026/11/14/nvidia-scandal/"
        res = ArticleExtractor.extract_article(url, html_text=SAMPLE_WAPO_HTML)
        self.assertTrue(res["is_substantive"])
        self.assertEqual(res["title"], "Nvidia scandal hits Trump’s political vulnerabilities after Democratic sweep")
        self.assertEqual(res["author"], "Isaac Arnsdorf and Cat Zakrzewski")
        self.assertEqual(res["paras_count"], 3)
        self.assertEqual(res["subheadings"], ["Political fallout on Capitol Hill"])
        self.assertNotIn("Most Read From The Washington Post", res["full_text"])

    def test_washsun_brightspot_and_avatar_block(self):
        url = "https://www.washingtonsun.com/technology/bank-ceos-nsa-tell-congress-ai-driven-patches-behind-outages"
        res = ArticleExtractor.extract_article(url, html_text=SAMPLE_WASHSUN_HTML)
        self.assertTrue(res["is_substantive"])
        self.assertEqual(res["title"], "Bank CEOs, NSA Tell Congress That AI-Driven Patches Are Behind Outages")
        self.assertEqual(res["author"], "Jeff Stein")
        self.assertEqual(res["paras_count"], 3)
        self.assertEqual(len(res["inline_images"]), 0)  # Author mugshot MUST be blocked
        self.assertNotIn("Sign up for The Washington Sun", res["full_text"])


if __name__ == "__main__":
    unittest.main()
