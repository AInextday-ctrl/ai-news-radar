#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.ifixit_crawler import crawl_ifixit, is_ifixit_url


SAMPLE_IFIXIT_HTML = """<!doctype html>
<html>
<head>
  <meta property="og:title" content="HomeView Teardown: A Surprising Step Backward - iFixit" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "HomeView Teardown: A Surprising Step Backward",
    "description": "A HomePod stuck to an iPad should not be this hard to repair.",
    "datePublished": "2026-11-18T13:33:49-08:00",
    "author": {"@type": "Person", "name": "Carsten Frauenheim"},
    "image": ["https://valkyrie.cdn.ifixit.com/media/2026/11/17111733/HomeView_00006.jpg"]
  }
  </script>
</head>
<body>
  <header>
    <div class="author-byline">
      <a href="https://www.ifixit.com/User/1">Carsten Frauenheim</a> with
      <a href="https://www.ifixit.com/User/2">Elizabeth Chamberlain</a> and
      <a href="https://www.ifixit.com/User/3">Shahram Mokhtari</a>
    </div>
  </header>
  <article>
    <div class="entry-content">
      <p>Apple’s first iPad-stuck-to-a-HomePod smarthome hub landed on our teardown table this week, and we found a surprising step backward in repairability.</p>
      <figure class="wp-block-embed is-type-video is-provider-youtube">
        <iframe src="https://www.youtube-nocookie.com/embed/rr7m9nBqDdo?feature=oembed" title="HomeView Teardown Video"></iframe>
      </figure>
      <h2>Glued Tighter Than an iPad?</h2>
      <p>Getting past the display required persistent heat and careful prying around brittle perimeter gaskets that tore almost immediately.</p>
      <figure class="wp-block-gallery has-nested-images">
        <figure class="wp-block-image">
          <img src="https://valkyrie.cdn.ifixit.com/media/2026/11/17111733/HomeView_00006-1200x800.jpg" alt="Duplicate cover resized" />
        </figure>
        <figure class="wp-block-image">
          <img src="https://valkyrie.cdn.ifixit.com/media/2026/11/17111734/HomeView_00007-1200x800.jpg" alt="HomeView display open" />
        </figure>
        <figcaption class="blocks-gallery-caption">Opening the HomeView display assembly.</figcaption>
      </figure>
      <div class="ifixit-promo-wrap alignfull">
        <h3>Legalize Repair T-Shirt</h3>
        <p>Don’t let corporate greed keep your tech limping along. Buy our shirt today.</p>
        <img src="https://valkyrie.cdn.ifixit.com/media/2026/11/shirt.jpg" alt="T-Shirt promo" />
      </div>
      <figure class="wp-block-image">
        <img src="https://valkyrie.cdn.ifixit.com/media/2026/11/17111750/HomeView_00017-2blog.jpg" alt="Connector carnage" />
        <figcaption>Connector carnage inside the speaker housing.</figcaption>
      </figure>
      <iframe src="https://voyager.lumafield.com/project/2f8c8e35?embed=true"></iframe>
      <p>Apple can do better, and its other modern hardware sold alongside HomeView proves repairability is a deliberate design choice.</p>
    </div>
  </article>
</body>
</html>
"""


class TestIFixitCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_ifixit_url("https://www.ifixit.com/News/120317/homeview-teardown-a-surprising-step-backward"))
        self.assertFalse(is_ifixit_url("https://www.cbsnews.com/news/marco-rubio-tech-outages-not-connected/"))

    def test_promo_strip_gallery_dedup_coauthors_and_youtube(self):
        res = crawl_ifixit(
            "https://www.ifixit.com/News/120317/homeview-teardown-a-surprising-step-backward",
            html_text=SAMPLE_IFIXIT_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Carsten Frauenheim, Elizabeth Chamberlain, and Shahram Mokhtari")
        self.assertIn("### Glued Tighter Than an iPad?", res["full_text"])
        self.assertNotIn("Legalize Repair T-Shirt", res["full_text"])
        self.assertNotIn("corporate greed", res["full_text"])
        # Cover resized duplicate (-1200x800) & promo shirt stripped; 2 real teardown photos kept in order
        self.assertEqual(len(res["inline_images"]), 2)
        self.assertIn("HomeView_00007-1200x800.jpg", res["inline_images"][0]["url"])
        self.assertEqual(res["inline_images"][0]["caption"], "Opening the HomeView display assembly.")
        self.assertEqual(res["inline_images"][0]["after_para"], 2)
        self.assertIn("HomeView_00017-2blog.jpg", res["inline_images"][1]["url"])
        # YouTube video extracted at exact slot; Lumafield WebGL iframe ignored
        self.assertTrue(res["has_video"])
        self.assertEqual(len(res["inline_videos"]), 1)
        self.assertEqual(res["inline_videos"][0]["video_id"], "rr7m9nBqDdo")
        self.assertEqual(res["inline_videos"][0]["after_para"], 0)


if __name__ == "__main__":
    unittest.main()
