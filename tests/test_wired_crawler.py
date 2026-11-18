#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for WIRED dedicated isolated crawler (`crawlers/wired_crawler.py`).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.wired_crawler import (
    crawl_wired,
    is_wired_url,
    _is_valid_wired_image,
    _wired_media_stem,
)
from article_extractor import ArticleExtractor


SAMPLE_WIRED_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Nvidia’s Board Has No Plans to Bring Back Jensen Huang | WIRED</title>
  <meta property="og:title" content="Nvidia’s Board Has No Plans to Bring Back Jensen Huang" />
  <meta property="og:image" content="https://media.wired.com/photos/6afce5159891667de5f2b6bb/191:100/w_1280,c_limit/Nvidia-Board.jpg" />
  <script type="application/ld+json">
    {"@type": "NewsArticle", "headline": "Nvidia’s Board Has No Plans to Bring Back Jensen Huang", "datePublished": "2026-11-17T17:19:19-05:00", "author": [{"@type": "Person", "name": "Lauren Goode"}]}
  </script>
  <script>window.__PRELOADED_STATE__ = {"transformed": {"article": {"headerProps": {"contributors": {"author": {"items": [{"name": "Lauren Goode"}, {"name": "Kate Taylor"}]}}}, "body": [["inline-embed", {"type": "cneinterlude", "props": {"interludeOverrideId": "6afb509689cc35ea8d45c201"}}]]}}};</script>
</head>
<body>
  <h1 data-testid="ContentHeaderHed">Nvidia’s Board Has No Plans to Bring Back Jensen Huang</h1>
  <div class="body__inner-container">
    <p>As Nvidia reported its third-quarter earnings on Tuesday, the company’s financial performance was overshadowed by ongoing questions about executive governance.</p>
    <h2>Board Governance Under Scrutiny</h2>
    <p>People close to the chipmaker’s board told WIRED that directors have made no plans to reinstate the former chief executive amid federal reviews.</p>
    <figure>
      <img src="https://media.wired.com/photos/6afce5159891667de5f2b6bb/master/w_1600/Nvidia-Board.jpg" alt="Duplicate cover" />
      <figcaption>Duplicate hero photo must be deduplicated by 24-hex photo ID.</figcaption>
    </figure>
    <figure>
      <img src="https://media.wired.com/photos/6afce5159891667de5f2b6cc/1:1/w_120,c_limit/lauren-goode.jpg" alt="Lauren Goode" />
      <figcaption>Author headshot must be blocked.</figcaption>
    </figure>
    <figure>
      <img src="https://media.wired.com/photos/6afce5159891667de5f2b6dd/16:9/w_1280/nvidia-hq.jpg" alt="Nvidia HQ" />
      <figcaption>Nvidia headquarters in Santa Clara, California.</figcaption>
    </figure>
    <p>Analysts said customer demand for next-generation AI accelerators remains strong despite leadership turbulence in Silicon Valley.</p>
    <p>Connect to what matters with the WIRED App. DOWNLOAD NOW</p>
    <p>Subscribe to WIRED for unlimited digital access.</p>
  </div>
</body>
</html>
"""


class TestWiredCrawler(unittest.TestCase):
    def test_url_and_image_validation(self):
        self.assertTrue(is_wired_url("https://www.wired.com/story/nvidias-board-has-no-plans-to-reinstate-jensen-huang/"))
        self.assertFalse(is_wired_url("https://www.ft.com/content/123"))
        self.assertTrue(_is_valid_wired_image("https://media.wired.com/photos/6afce5159891667de5f2b6bb/191:100/w_1280,c_limit/Nvidia-Board.jpg"))
        self.assertFalse(_is_valid_wired_image("https://media.wired.com/photos/6afce5159891667de5f2b6cc/1:1/w_120,c_limit/lauren-goode.jpg"))
        self.assertEqual(
            _wired_media_stem("https://media.wired.com/photos/6afce5159891667de5f2b6bb/191:100/w_1280,c_limit/Nvidia-Board.jpg"),
            "6afce5159891667de5f2b6bb",
        )

    def test_wired_extraction_and_routing(self):
        url = "https://www.wired.com/story/nvidias-board-has-no-plans-to-reinstate-jensen-huang/"
        res = ArticleExtractor.extract_article(url, html_text=SAMPLE_WIRED_HTML)
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertEqual(res["title"], "Nvidia’s Board Has No Plans to Bring Back Jensen Huang")
        self.assertEqual(res["author"], "Lauren Goode and Kate Taylor")
        self.assertTrue(res["has_video"])
        self.assertEqual(res["video_provider"], "iframe")
        self.assertEqual(res["video_url"], "https://player.cnevids.com/iframe/video/6afb509689cc35ea8d45c201")
        self.assertEqual(res["paras_count"], 3)
        self.assertEqual(res["subheadings"], ["Board Governance Under Scrutiny"])
        self.assertNotIn("Subscribe to WIRED", res["full_text"])
        self.assertNotIn("WIRED App", res["full_text"])
        # Duplicate cover + 1:1 author avatar both rejected; only distinct HQ photo kept
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertIn("6afce5159891667de5f2b6dd", res["inline_images"][0]["url"])


if __name__ == "__main__":
    unittest.main()
