#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.bbc_crawler import crawl_bbc, is_bbc_url


SAMPLE_BBC_HTML = """<!doctype html>
<html>
<head>
  <meta property="og:title" content="NHS data contract to stay with Palantir until 2029 - BBC News" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "ReportageNewsArticle",
    "headline": "NHS data contract to stay with controversial US tech giant Palantir until 2029",
    "datePublished": "2026-11-17T12:00:12.778Z",
    "author": [{"@type": "Person", "name": "Hugh Pym"}],
    "image": {
      "@type": "ImageObject",
      "url": "https://ichef.bbci.co.uk/news/1024/branded_news/87b8/live/b2aca760-54fb-11f1-b682-cf91850925ea.jpg"
    }
  }
  </script>
</head>
<body>
  <article>
    <div data-component="headline-block"><h1>NHS data contract to stay with Palantir until 2029</h1></div>
    <div data-component="byline-block">1 day ago Share Save Hugh Pym</div>
    <div data-component="image-block">
      <img src="https://static.files.bbci.co.uk/grey-placeholder.png" alt="" />
      <img src="https://ichef.bbci.co.uk/news/480/cpsprodpb/87b8/live/b2aca760-54fb-11f1-b682-cf91850925ea.jpg.webp" alt="Duplicate cover UUID" />
    </div>
    <div data-component="text-block"><p>The government says it will continue a key NHS data contract in England with the controversial US tech giant Palantir until 2029.</p></div>
    <div data-component="subheadline-block"><h2>'Albatross around the NHS's neck'</h2></div>
    <div data-component="text-block"><p>The £330m deal, which began in 2024 to help manage hospital waiting lists in England, was due to run for five years with an option to extend.</p></div>
    <div data-component="image-block">
      <img src="https://static.files.bbci.co.uk/grey-placeholder.png" alt="" />
      <img src="https://ichef.bbci.co.uk/news/480/cpsprodpb/b53c/live/064b8810-e1f0-11f1-99b6-a35a62fa4264.jpg.webp" srcset="https://ichef.bbci.co.uk/news/1024/cpsprodpb/b53c/live/064b8810-e1f0-11f1-99b6-a35a62fa4264.jpg.webp 1024w" alt="Hospital corridor" />
      <figcaption>NHS hospitals across England use the federated data platform.</figcaption>
    </div>
    <div data-component="text-block"><p>Palantir UK said it was right to press forward with the programme which was exceeding targets and helping deliver more operations across trusts.</p></div>
    <div data-component="links-block"><p>Related stories on Palantir</p></div>
    <div data-component="image-block">
      <img src="https://ichef.bbci.co.uk/news/480/cpsprodpb/41d3/live/348b21e0-26a8-11f0-8f57-b7237f6a66e6.png.webp" alt="A green promotional banner with black squares" />
    </div>
    <div data-component="text-block"><p>Sign up for our Tech Decoded newsletter to follow the world's top tech stories and trends.</p></div>
    <div data-component="tag-list-block"><p>Data protection NHS</p></div>
  </article>
</body>
</html>
"""


class TestBBCCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_bbc_url("https://www.bbc.com/news/articles/cqvg27zpm8w8o"))
        self.assertTrue(is_bbc_url("https://www.bbc.co.uk/news/articles/cq99exy89dngo"))
        self.assertFalse(is_bbc_url("https://www.tomshardware.com/pc-components/gpus/nvidia"))

    def test_data_components_uuid_dedup_and_newsletter_hard_stop(self):
        res = crawl_bbc(
            "https://www.bbc.com/news/articles/cqvg27zpm8w8o",
            html_text=SAMPLE_BBC_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Hugh Pym")
        self.assertIn("### 'Albatross around the NHS's neck'", res["full_text"])
        self.assertNotIn("Tech Decoded newsletter", res["full_text"])
        self.assertNotIn("Related stories on Palantir", res["full_text"])
        # Duplicate cover UUID & grey-placeholder & post-links promo banner stripped; 1 HD srcset inline image kept
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertIn("/news/1024/", res["inline_images"][0]["url"])
        self.assertEqual(res["inline_images"][0]["after_para"], 2)


if __name__ == "__main__":
    unittest.main()
