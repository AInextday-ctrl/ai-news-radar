#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.cbsnews_crawler import crawl_cbsnews, is_cbsnews_url


SAMPLE_CBSNEWS_HTML = """<!doctype html>
<html>
<head>
  <meta property="og:title" content="Rubio says there's zero evidence tech outages are related - CBS News" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Rubio says there's \\"zero evidence\\" recent tech outages are related",
    "description": "Secretary of State Marco Rubio addressed recent U.S. tech disruptions.",
    "datePublished": "2026-11-17T21:43:00-0500",
    "author": [
      {"@type": "Person", "name": "Kiki  Intarasuwan"},
      {"@type": "Person", "name": "Nicole  Sganga"}
    ],
    "image": {
      "@type": "ImageObject",
      "url": "https://assets3.cbsnewsstatic.com/hub/i/r/2026/11/18/dd4ffecc-82ca-4351-9b61-50732f9a9014/thumbnail/1200x630/hash1/getty.jpg"
    }
  }
  </script>
</head>
<body>
  <figure id="breaking-news" class="breaking-news"><video src="https://example.com/live.m3u8"></video></figure>
  <article>
    <section class="content__body">
      <p>Secretary of State Marco Rubio said there's "zero evidence" that recent tech outages in U.S. air travel and banking are connected.</p>
      <div class="embed__float-wrap">
        <figure class="embed embed--type-image is-image">
          <img src="https://assets2.cbsnewsstatic.com/hub/i/r/2026/11/18/dd4ffecc-82ca-4351-9b61-50732f9a9014/thumbnail/620x434g2/hash2/getty.jpg#" alt="Duplicate cover UUID" />
        </figure>
      </div>
      <p>On Thursday, Microsoft said it experienced a worldwide outage affecting Outlook and Teams across enterprise customers worldwide.</p>
      <div class="embed__float-wrap">
        <figure class="embed embed--type-image is-image">
          <img src="https://assets2.cbsnewsstatic.com/hub/i/r/2026/11/18/aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb/thumbnail/620x434/hash3/airport.jpg#" alt="Airport departure board" />
          <figcaption>Travelers check flight boards during the FAA ground stop. (Getty Images)</figcaption>
        </figure>
      </div>
      <h3>Federal officials weigh in</h3>
      <figure class="embed embed--type-video is-video">
        <iframe data-src="https://www.cbsnews.com/embed/video/?optanonConsent=0&amp;v=abc123456" title="Rubio addresses tech outages"></iframe>
      </figure>
      <p>Democratic Sen. Mark Warner said intelligence officials have seen no indication of a coordinated cyberattack targeting critical infrastructure.</p>
      <p>WEB EXCLUSIVE: Watch an extended interview with officials (Video)</p>
      <p>Story produced by Emily Pandise. Editor: Emanuele Secci.</p>
      <p>In:</p>
    </section>
  </article>
</body>
</html>
"""


class TestCBSNewsCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_cbsnews_url("https://www.cbsnews.com/news/marco-rubio-tech-outages-not-connected/"))
        self.assertFalse(is_cbsnews_url("https://www.coindesk.com/business/2026/11/17/solana"))

    def test_uuid_cover_dedup_authors_and_video(self):
        res = crawl_cbsnews(
            "https://www.cbsnews.com/news/marco-rubio-tech-outages-not-connected/",
            html_text=SAMPLE_CBSNEWS_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Kiki Intarasuwan and Nicole Sganga")
        self.assertIn("### Federal officials weigh in", res["full_text"])
        self.assertNotIn("WEB EXCLUSIVE", res["full_text"])
        self.assertNotIn("Story produced by", res["full_text"])
        self.assertNotIn("In:", res["full_text"])
        # Duplicate cover UUID across assets3 vs assets2 stripped; distinct UUID kept without trailing #
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertFalse(res["inline_images"][0]["url"].endswith("#"))
        self.assertIn("aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb", res["inline_images"][0]["url"])
        self.assertEqual(res["inline_images"][0]["after_para"], 1)
        # CBS video iframe extracted cleanly into inline_videos
        self.assertTrue(res["has_video"])
        self.assertEqual(len(res["inline_videos"]), 1)
        self.assertEqual(res["inline_videos"][0]["video_id"], "abc123456")
        self.assertEqual(res["inline_videos"][0]["after_para"], 2)


if __name__ == "__main__":
    unittest.main()
