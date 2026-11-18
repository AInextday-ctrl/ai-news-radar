#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.nypost_crawler import crawl_nypost, is_nypost_url


SAMPLE_NYPOST_HTML = """<!doctype html>
<html>
<head>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Exclusive | How ex-Nvidia CEO Jensen Huang managed executive meetings",
    "datePublished": "2026-11-16T14:46:32Z",
    "author": [{"@type": "Person", "name": "Emily Goodin"}],
    "image": {"@type": "ImageObject", "url": "https://nypost.com/wp-content/uploads/sites/2/2026/11/cover.jpg?w=1200"}
  }
  </script>
</head>
<body>
  <article>
    <div class="single__content entry-content">
      <p>WASHINGTON — President Donald Trump said Monday he would not mind seeing Jensen Huang reinstated as Nvidia CEO following recent leadership changes.</p>
      <figure class="nyp-slideshow-modal-image wp-block-image">
        <img src="https://nypost.com/wp-content/uploads/sites/2/2026/11/trump-lawn.jpg?w=1024" alt="Trump on South Lawn" />
        <figcaption>3 President Donald Trump speaks with reporters on the South Lawn of the White House.</figcaption>
      </figure>
      <div class="ad ad--container"><p>Advertisement</p></div>
      <h2 class="wp-block-heading">Here’s the latest on the Nvidia CEO’s departure:</h2>
      <ul>
        <li><a href="https://nypost.com/2026/11/15/related-story/">Related NY Post link that should be skipped</a></li>
      </ul>
      <p>Nvidia chief financial officer Colette Kress has taken over as interim CEO while the company's board searches for a permanent successor to lead the chipmaker.</p>
      <div class="wp-block-nyp-editor-universal-promo"><p>Sign up for our daily newsletter</p></div>
      <p>The president said he did not expect to discuss chip sales during upcoming bilateral meetings with foreign leaders in Asia this week.</p>
    </div>
  </article>
</body>
</html>
"""


class TestNYPostCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_nypost_url("https://nypost.com/2026/11/16/us-news/trump-jensen-huang/"))
        self.assertFalse(is_nypost_url("https://www.bbc.com/news/articles/cqvg27zpm8w8o"))

    def test_eyebrow_caption_digits_and_crosslink_cleanup(self):
        res = crawl_nypost(
            "https://nypost.com/2026/11/16/us-news/trump-jensen-huang/",
            html_text=SAMPLE_NYPOST_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "How ex-Nvidia CEO Jensen Huang managed executive meetings")
        self.assertEqual(res["author"], "Emily Goodin")
        self.assertNotIn("Here’s the latest on", res["full_text"])
        self.assertNotIn("Related NY Post link", res["full_text"])
        self.assertNotIn("Advertisement", res["full_text"])
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertTrue(res["inline_images"][0]["caption"].startswith("President Donald Trump"))
        self.assertEqual(res["inline_images"][0]["after_para"], 0)


if __name__ == "__main__":
    unittest.main()
