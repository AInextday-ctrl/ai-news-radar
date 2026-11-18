#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Financial Times dedicated isolated crawler (`crawlers/ft_crawler.py`).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.ft_crawler import (
    crawl_ft,
    is_ft_url,
    _is_valid_ft_image,
    _ft_media_stem,
)
from article_extractor import ArticleExtractor


SAMPLE_FT_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Plural raises €1bn fund to back European tech start-ups | Financial Times</title>
  <meta property="og:title" content="Plural raises €1bn fund to back European tech start-ups" />
  <meta property="og:image" content="https://images.ft.com/v3/image/raw/https%3A%2F%2Fd1e00ek4ebabms.cloudfront.net%2Fproduction%2F15e21b6f-8c7a-414d-ab8d-ca1234567890.jpg?source=next-article" />
  <script type="application/ld+json">
    {"@type": "NewsArticle", "headline": "Plural raises €1bn fund to back European tech start-ups", "datePublished": "2026-11-17T06:00:00Z"}
  </script>
</head>
<body>
  <h1 class="o-topper__headline">Plural raises €1bn fund to back European tech start-ups</h1>
  <div class="n-content-byline">
    <a data-trackable="author" href="/rachel-rees">Rachel Rees</a>
    <a data-trackable="author" href="/tim-bradshaw">Tim Bradshaw</a>
  </div>
  <div class="n-content-body">
    <p>Simply sign up to the Technology myFT Digest -- delivered directly to your inbox.</p>
    <p>One of Europe’s most ambitious tech investors has raised €1bn to back the continent’s start-ups in a milestone for venture capital funding.</p>
    <h2>Scaling European Deep Tech</h2>
    <p>Plural said the new fund will focus on frontier artificial intelligence, robotics, and energy infrastructure founders across Europe.</p>
    <figure>
      <img src="https://images.ft.com/v3/image/raw/https%3A%2F%2Fd1e00ek4ebabms.cloudfront.net%2Fproduction%2F15e21b6f-8c7a-414d-ab8d-ca1234567890.jpg?width=700" alt="Duplicate cover" />
      <figcaption>Duplicate cover should be stripped by UUID stem.</figcaption>
    </figure>
    <figure>
      <img src="https://images.ft.com/v3/image/raw/https%3A%2F%2Fd1e00ek4ebabms.cloudfront.net%2Fproduction%2F8c557039-f6ec-42ed-b50d-76177fa95c49.jpg?width=700" alt="Founders summit" />
      <figcaption>Plural partners at the London founders summit.</figcaption>
    </figure>
    <p>Partners argued that European founders increasingly have the technical talent required to build globally competitive companies without relocating to Silicon Valley.</p>
    <p>Unlock the Editor’s Digest for free.</p>
  </div>
</body>
</html>
"""


class TestFtCrawler(unittest.TestCase):
    def test_url_and_image_validation(self):
        self.assertTrue(is_ft_url("https://www.ft.com/content/26e52d2a-b259-4283-af83-e2c75d67a2fc"))
        self.assertFalse(is_ft_url("https://www.nytimes.com/2026/11/17/test.html"))
        self.assertTrue(_is_valid_ft_image("https://images.ft.com/v3/image/raw/https%3A%2F%2Fd1e00ek4ebabms.cloudfront.net%2Fproduction%2F15e21b6f-8c7a-414d-ab8d-ca1234567890.jpg"))
        self.assertFalse(_is_valid_ft_image("https://images.ft.com/v3/image/raw/author-headshot.jpg"))
        self.assertEqual(
            _ft_media_stem("https://images.ft.com/v3/image/raw/https%3A%2F%2Fd1e00ek4ebabms.cloudfront.net%2Fproduction%2F15e21b6f-8c7a-414d-ab8d-ca1234567890.jpg?width=700"),
            "15e21b6f-8c7a-414d-ab8d-ca1234567890",
        )

    def test_ft_extraction_and_routing(self):
        url = "https://www.ft.com/content/26e52d2a-b259-4283-af83-e2c75d67a2fc"
        res = ArticleExtractor.extract_article(url, html_text=SAMPLE_FT_HTML)
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertEqual(res["title"], "Plural raises €1bn fund to back European tech start-ups")
        self.assertEqual(res["author"], "Rachel Rees and Tim Bradshaw")
        self.assertEqual(res["paras_count"], 3)
        self.assertEqual(res["subheadings"], ["Scaling European Deep Tech"])
        self.assertNotIn("myFT Digest", res["full_text"])
        self.assertNotIn("Editor’s Digest", res["full_text"])
        # Cover UUID duplicate stripped; distinct inline photo kept
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertIn("8c557039-f6ec-42ed-b50d-76177fa95c49", res["inline_images"][0]["url"])


if __name__ == "__main__":
    unittest.main()
