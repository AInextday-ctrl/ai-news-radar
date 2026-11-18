#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for The New York Times dedicated isolated crawler (`crawlers/nyt_crawler.py`).
Covers:
  1. URL detection & canonical cache key normalization
  2. Tier 1 `window.__preloadedData` GraphQL AST parsing (including JS `undefined` literals),
     multi-author attribution, subheadings, cover rendition priority, cover-stem inline
     deduplication, and avatar/logo rejection
  3. Tier 2 DOM + JSON-LD fallback with space-safe inline link parsing & NYT subscription
     boilerplate stripping
  4. `ArticleExtractor` isolated routing to `crawl_nyt`
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.nyt_crawler import (
    crawl_nyt,
    is_nyt_url,
    _is_valid_nyt_image,
    _nyt_media_stem,
)
from article_extractor import ArticleExtractor


SAMPLE_NYT_PRELOADED_HTML = """<!DOCTYPE html>
<html>
<head><title>A.I. Helps Find Major Security Bug in Java - The New York Times</title></head>
<body>
<script>window.__preloadedData = {
  "loaderData": {
    "data": {
      "article": {
        "__typename": "Article",
        "headline": {"default": "A.I. Helps Find Major Security Bug in Java", "seo": undefined},
        "summary": "The discovery shows A.I. systems finding critical flaws in enterprise software.",
        "firstPublished": "2026-11-17T21:05:54.000Z",
        "bylines": [
          {
            "creators": [
              {"displayName": "Dustin Volz"},
              {"displayName": "Dylan Freedman"}
            ],
            "renderedRepresentation": "By Dustin Volz and Dylan Freedman"
          }
        ],
        "promotionalMedia": {
          "assetCrops": [
            {
              "renditions": [
                {"name": "mediumSquareAt3X", "width": 1800, "height": 1800, "url": "https://static01.nyt.com/images/2026/11/17/multimedia/17dc-aibug-zfmc/17dc-aibug-zfmc-mediumSquareAt3X.jpg"},
                {"name": "videoSixteenByNineJumbo1600", "width": 1600, "height": 900, "url": "https://static01.nyt.com/images/2026/11/17/multimedia/17dc-aibug-zfmc/17dc-aibug-zfmc-videoSixteenByNineJumbo1600.jpg"}
              ]
            }
          ]
        },
        "sprinkledBody": {
          "content": [
            {"__typename": "HeaderBasicBlock", "ledeMedia": undefined},
            {
              "__typename": "ParagraphBlock",
              "content": [
                {"text": "A cybersecurity start-up revealed on Tuesday it had used a new A.I. model to uncover a critical software bug in Java, a foundation of enterprise computing."}
              ]
            },
            {"__typename": "Dropzone", "id": "ad-1"},
            {
              "__typename": "Heading2Block",
              "content": [{"text": "A New Era for Automated Security Audits"}]
            },
            {
              "__typename": "ParagraphBlock",
              "content": [
                {"text": "Using leading A.I. models, the start-up Calif has now "},
                {"text": "unearthed a string of serious vulnerabilities"},
                {"text": " in widely deployed open-source systems over recent months."}
              ]
            },
            {
              "__typename": "ImageBlock",
              "media": {
                "assetCrops": [
                  {
                    "renditions": [
                      {"name": "articleLarge", "width": 600, "height": 400, "url": "https://static01.nyt.com/images/2026/11/17/multimedia/17dc-aibug-zfmc/17dc-aibug-zfmc-articleLarge.jpg"}
                    ]
                  }
                ],
                "caption": {"text": "Duplicate cover photo should be deduplicated."},
                "credit": "The New York Times"
              }
            },
            {
              "__typename": "ImageBlock",
              "media": {
                "assetCrops": [
                  {
                    "renditions": [
                      {"name": "threeByTwoLargeAt2X", "width": 1600, "height": 1067, "url": "https://static01.nyt.com/images/2026/11/17/multimedia/17dc-aibug-lab/17dc-aibug-lab-threeByTwoLargeAt2X.jpg"}
                    ]
                  }
                ],
                "caption": {"text": "Researchers analyzing the Java runtime exploit."},
                "credit": "Haiyun Jiang for The New York Times"
              }
            },
            {
              "__typename": "ParagraphBlock",
              "content": [
                {"text": "Industry executives said the milestone underscores how quickly frontier models are reshaping both offensive and defensive cybersecurity operations worldwide."}
              ]
            },
            {
              "__typename": "ParagraphBlock",
              "content": [{"text": "Want all of The Times? Subscribe."}]
            }
          ]
        }
      }
    }
  }
};</script>
</body>
</html>
"""

SAMPLE_NYT_DOM_FALLBACK_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>F.A.A. Shelves Routers Linked to Ground Stop - The New York Times</title>
  <meta property="og:image" content="https://static01.nyt.com/images/2026/11/17/multimedia/17xp-faa-routers-tmwk/17xp-faa-routers-tmwk-facebookJumbo.jpg" />
  <script type="application/ld+json">
    {"@type": "NewsArticle", "headline": "F.A.A. Shelves Routers Linked to Ground Stop", "datePublished": "2026-11-17T20:00:00Z", "author": [{"@type": "Person", "name": "Nirajteja Chokshi"}]}
  </script>
</head>
<body>
  <article>
    <h1 data-testid="headline">F.A.A. Shelves Routers Linked to Ground Stop</h1>
    <section name="articleBody">
      <p>The Federal Aviation Administration has paused installations of Juniper routers after an outage <a href="/link">disrupted flights nationwide</a> earlier this week.</p>
      <p>Agency officials confirmed that backup routing equipment has been activated across major air traffic control centers while engineers complete firmware audits.</p>
      <p>Aviation safety regulators said passengers should expect normal schedules as redundancy tests continue through the remainder of the month.</p>
      <p>Thank you for your patience while we verify access. Already a subscriber? Log in.</p>
      <p>Want all of The Times? Subscribe.</p>
    </section>
  </article>
</body>
</html>
"""


class TestNytCrawler(unittest.TestCase):
    def test_url_and_image_validation(self):
        self.assertTrue(is_nyt_url("https://www.nytimes.com/2026/11/17/us/faa-routers-ground-stop.html?unlocked_article_code=1.RVE"))
        self.assertTrue(is_nyt_url("https://nyti.ms/abc123"))
        self.assertFalse(is_nyt_url("https://www.wsj.com/tech/ai"))
        self.assertTrue(_is_valid_nyt_image("https://static01.nyt.com/images/2026/11/17/multimedia/17dc-aibug-zfmc/17dc-aibug-zfmc-videoSixteenByNineJumbo1600.jpg"))
        self.assertFalse(_is_valid_nyt_image("https://static01.nyt.com/images/2026/11/17/author-headshot.jpg"))
        self.assertFalse(_is_valid_nyt_image("https://static01.nyt.com/images/2026/11/17/foo/foo-thumbStandard.jpg"))
        self.assertEqual(
            _nyt_media_stem("https://static01.nyt.com/images/2026/11/17/multimedia/17dc-aibug-zfmc/17dc-aibug-zfmc-articleLarge.jpg"),
            "17dc-aibug-zfmc",
        )

    def test_preloaded_graphql_extraction(self):
        url = "https://www.nytimes.com/2026/11/17/us/politics/ai-security-bug-java.html?unlocked_article_code=1.RFE.J4uR"
        res = crawl_nyt(url, html_text=SAMPLE_NYT_PRELOADED_HTML, localize_cover=False, use_cache=False)
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertEqual(res["title"], "A.I. Helps Find Major Security Bug in Java")
        self.assertEqual(res["author"], "Dustin Volz and Dylan Freedman")
        self.assertEqual(res["paras_count"], 3)
        self.assertIn("unearthed a string of serious vulnerabilities", res["full_text"])
        self.assertNotIn("Want all of The Times", res["full_text"])
        self.assertEqual(res["subheadings"], ["A New Era for Automated Security Audits"])
        self.assertIn("videoSixteenByNineJumbo1600.jpg", res["cover_image"])
        # Cover stem duplicate must be stripped; genuine inline photo preserved with credit
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertIn("17dc-aibug-lab-threeByTwoLargeAt2X.jpg", res["inline_images"][0]["url"])
        self.assertIn("Haiyun Jiang", res["inline_images"][0]["caption"])

    def test_dom_fallback_and_article_extractor_routing(self):
        url = "https://www.nytimes.com/2026/11/17/us/faa-routers-ground-stop.html"
        res = ArticleExtractor.extract_article(url, html_text=SAMPLE_NYT_DOM_FALLBACK_HTML)
        self.assertTrue(res["is_substantive"])
        self.assertEqual(res["title"], "F.A.A. Shelves Routers Linked to Ground Stop")
        self.assertEqual(res["author"], "Nirajteja Chokshi")
        self.assertEqual(res["paras_count"], 3)
        # Ensure space around <a> tag was preserved
        self.assertIn("outage disrupted flights nationwide earlier", res["full_text"])
        self.assertNotIn("Thank you for your patience", res["full_text"])
        self.assertNotIn("Want all of The Times", res["full_text"])
        self.assertIn("17xp-faa-routers-tmwk-facebookJumbo.jpg", res["cover_image"])


if __name__ == "__main__":
    unittest.main()
