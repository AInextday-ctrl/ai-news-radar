#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for isolated IGN dedicated crawler (`crawlers/ign_crawler.py`).
"""

import json
import unittest
from crawlers.ign_crawler import is_ign_url, extract_ign_article


SAMPLE_APOLLO = {
    "Contributor:c1": {"__typename": "Contributor", "name": "Luke Reilly"},
    "Contributor:c2": {"__typename": "Contributor", "name": "Simon Cardy"},
    "Image:img1": {
        "__typename": "Image",
        "url": "https://assets-prd.ignimgs.com/2026/11/18/photo-1.jpg",
        "caption": "Vice City skyline at dusk.",
    },
    "Image:img2": {
        "__typename": "Image",
        "url": "https://assets-prd.ignimgs.com/2026/11/18/photo-2.jpg",
        "caption": "Leonida coastal highway during a tropical storm.",
    },
    "ModernContent:ss1": {
        "__typename": "ModernContent",
        "id": "ss1",
        "type": "Slideshow",
        "title": "GTA 6 Gallery",
    },
    "ModernContent:hv1": {
        "__typename": "ModernContent",
        "id": "hv1",
        "type": "Video",
        "title": "How Long Is GTA 6?",
        "feedImage": {"url": "https://assets-prd.ignimgs.com/2026/11/18/hv-poster.jpg"},
    },
    'ModernVideo:{"content":{"id":"hv1"}}': {
        "__typename": "ModernVideo",
        "isShort": False,
        "content": {"__ref": "ModernContent:hv1"},
        "assets": [
            {"url": "https://assets.ign.com/videos/640/hv1.mp4", "width": 640, "height": 360},
            {"url": "https://assets.ign.com/videos/1280/hv1.mp4", "width": 1280, "height": 720},
        ],
    },
    "ModernContent:iv1": {
        "__typename": "ModernContent",
        "id": "iv1",
        "type": "Video",
        "title": "GTA 6 Review Video",
        "feedImage": {"url": "https://assets-prd.ignimgs.com/2026/11/18/iv-poster.jpg"},
    },
    'ModernVideo:{"content":{"id":"iv1"}}': {
        "__typename": "ModernVideo",
        "isShort": False,
        "content": {"__ref": "ModernContent:iv1"},
        "assets": [
            {"url": "https://assets.ign.com/videos/1280/iv1.mp4", "width": 1280, "height": 720},
        ],
    },
    "ModernContent:art1": {
        "__typename": "ModernContent",
        "id": "art1",
        "type": "Article",
        "title": "How Long Is GTA 6? - IGN",
        "subtitle": "Short deck",
        "publishDate": "2026-11-18T11:00:00.000Z",
        "feedImage": {"url": "https://assets-prd.ignimgs.com/2026/11/18/cover.jpg"},
        "contributorsOrBylines": [
            {"__ref": "Contributor:c1"},
            {"__ref": "Contributor:c2"},
        ],
    },
    'ModernArticle:{"content":{"id":"art1"}}': {
        "__typename": "ModernArticle",
        "content": {"__ref": "ModernContent:art1"},
        "article": {
            "heroVideoContentId": "hv1",
            "heroVideoContentSlug": "how-long-is-gta-6",
            "processedHtml": """
            <section class="article-page">
              <p>In every sense of the word, Grand Theft Auto 6 is a massive open-world game spanning Leonida.</p>
              <section data-transform="mobile-ad-break"></section>
              <h2>Campaign Playtimes</h2>
              <h3>Completion Time: 70 hours</h3>
              <ul>
                <li>Our fastest reviewer finished the main story in 42 hours.</li>
                <li>Our most thorough reviewer spent 115 hours exploring side missions.</li>
              </ul>
              <section data-transform="slideshow" data-slug="gta-6-gallery"></section>
              <p>Players tackling side activities and character missions will easily cross 70 hours before seeing credits roll.</p>
              <section data-transform="ignvideo" data-slug="gta-6-review"></section>
              <p>Even after the credits, dozens of strangers, random encounters, and collectibles remain across the map.</p>
              <p>For more GTA 6, make sure to check out our review, or head over to our launch live blog.</p>
              <aside><h2>GTA 6 on IGN - The Biggest Stories at Launch</h2><p>Promo box text that must be stripped.</p></aside>
              <section data-transform="poll" data-id="poll-1"></section>
              <section data-transform="divider"></section>
              <section data-transform="author-sign-off" data-id="c1"></section>
              <p>Author bio paragraph that must never appear in article body.</p>
            </section>
            """,
        },
    },
    "ROOT_QUERY": {
        'slideshow({"queryBy":"slug","value":"gta-6-gallery"})': {
            "content": {"__ref": "ModernContent:ss1"},
            "slideshowImages:{}": {
                "images": [
                    {"__ref": "Image:img1"},
                    {"__ref": "Image:img2"},
                ]
            },
        },
        'videoBySlug({"slug":"gta-6-review"})': {
            "__ref": 'ModernVideo:{"content":{"id":"iv1"}}',
        },
    },
}

SAMPLE_HTML_APOLLO = f"""<!doctype html>
<html>
<head>
  <meta property="og:description" content="We tasked four reviewers with completing Grand Theft Auto 6 from start to finish to measure realistic campaign completion times." />
  <meta property="og:image" content="https://assets-prd.ignimgs.com/2026/11/18/cover.jpg" />
</head>
<body>
  <script id="__NEXT_DATA__" type="application/json">{json.dumps({"props": {"apolloState": SAMPLE_APOLLO}})}</script>
</body>
</html>
"""

SAMPLE_HTML_DOM_FALLBACK = """<!doctype html>
<html>
<head>
  <title>Sony Issues Official PS5 Firmware Update Warning - IGN</title>
  <meta property="og:description" content="Sony confirmed PS5 firmware 14.23 is mandatory ahead of GTA 6 launch." />
  <meta property="og:image" content="https://assets-prd.ignimgs.com/2025/02/26/ps5console.jpeg" />
  <script type="application/ld+json">
  {
    "@type": "NewsArticle",
    "headline": "Sony Issues Official PS5 Firmware Update Warning",
    "datePublished": "2026-11-18T07:33:45.941Z",
    "author": {"@type": "Person", "name": "Wesley Yin-Poole"}
  }
  </script>
</head>
<body>
  <main>
    <h1>Sony Issues Official PS5 Firmware Update Warning</h1>
    <section class="article-page">
      <p>Sony has confirmed that the recently released PS5 firmware 14.23 update is required to play GTA 6 ahead of its global midnight launch.</p>
      <h2>Why has Sony issued this PS5 update warning?</h2>
      <p>Industry observers believe the mandatory system software update cuts PlayStation Network access on older firmware to counter recent homebrew jailbreaks.</p>
      <p>Take-Two Interactive CEO Strauss Zelnick recently told IGN that the company is closely monitoring piracy and AI-assisted reverse-engineering risks across modern consoles.</p>
      <div data-cy="accent-divider"></div>
      <p>Wesley is IGN's Managing Editor. Follow him on Twitter.</p>
    </section>
  </main>
</body>
</html>
"""


class TestIGNCrawler(unittest.TestCase):
    def test_url_matching(self):
        self.assertTrue(is_ign_url("https://www.ign.com/articles/how-long-is-gta-6"))
        self.assertTrue(is_ign_url("https://ign.com/articles/test"))
        self.assertTrue(is_ign_url("https://uk.ign.com/articles/test"))
        self.assertFalse(is_ign_url("https://www.design.com/articles/test"))
        self.assertFalse(is_ign_url("https://sign.com/news/test"))
        self.assertFalse(is_ign_url(""))

    def test_apollo_extraction_media_and_cleanup(self):
        res = extract_ign_article(
            "https://www.ign.com/articles/how-long-is-gta-6",
            use_cache=False,
            localize_cover=False,
            html_text=SAMPLE_HTML_APOLLO,
            resolve_inline_videos=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_substantive"])
        self.assertEqual(res["title"], "How Long Is GTA 6?")
        self.assertEqual(res["author"], "Luke Reilly and Simon Cardy")
        self.assertIn("four reviewers", res["summary"])
        self.assertIn("### Campaign Playtimes", res["paragraphs"])
        # h3 preserves secondary heading hierarchy (`#### `) below h2 (`### `)
        self.assertIn("#### Completion Time: 70 hours", res["paragraphs"])
        self.assertNotIn("### Completion Time: 70 hours", res["paragraphs"])
        # Bullet list preserved cleanly
        self.assertTrue(any(p.startswith("• Our fastest reviewer") for p in res["paragraphs"]))
        # Slideshow images resolved with captions
        self.assertEqual(len(res["inline_images"]), 2)
        self.assertEqual(res["inline_images"][0]["caption_en"], "Vice City skyline at dusk.")
        # Hero video (after_para=-1) + Inline video (after_para>=0) both present
        self.assertEqual(len(res["inline_videos"]), 2)
        self.assertEqual(res["inline_videos"][0]["after_para"], -1)
        self.assertEqual(res["inline_videos"][0]["url"], "https://assets.ign.com/videos/1280/hv1.mp4")
        self.assertGreaterEqual(res["inline_videos"][1]["after_para"], 0)
        self.assertEqual(res["inline_videos"][1]["url"], "https://assets.ign.com/videos/1280/iv1.mp4")
        # Promo tail, aside box, and author bio hard-stopped
        self.assertNotIn("make sure to check out our review", res["full_text"])
        self.assertNotIn("Promo box text", res["full_text"])
        self.assertNotIn("Author bio paragraph", res["full_text"])

    def test_dom_fallback_extraction(self):
        res = extract_ign_article(
            "https://www.ign.com/articles/sony-ps5-firmware",
            use_cache=False,
            localize_cover=False,
            html_text=SAMPLE_HTML_DOM_FALLBACK,
            resolve_inline_videos=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_substantive"])
        self.assertEqual(res["title"], "Sony Issues Official PS5 Firmware Update Warning")
        self.assertEqual(res["author"], "Wesley Yin-Poole")
        self.assertIn("### Why has Sony issued this PS5 update warning?", res["paragraphs"])
        self.assertNotIn("Managing Editor", res["full_text"])


if __name__ == "__main__":
    unittest.main()
