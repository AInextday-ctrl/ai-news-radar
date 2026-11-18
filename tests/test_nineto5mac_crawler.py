#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.nineto5mac_crawler import crawl_nineto5mac, is_nineto5mac_url


SAMPLE_N95M_HTML = """<!doctype html>
<html>
<head>
  <meta property="og:title" content="Mount Thor raises $45 million to build Mac data centers for AI agents - 9to5Mac" />
  <meta property="og:image" content="https://9to5mac.com/wp-content/uploads/sites/6/2026/11/AI-Apple-2.jpg?resize=1200,628" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Article",
        "headline": "Mount Thor raises $45 million to build Mac data centers for AI agents",
        "datePublished": "2026-11-12T14:00:00+00:00",
        "author": {"name": "Bradley C"}
      }
    ]
  }
  </script>
</head>
<body>
  <article>
    <div class="container med post-content">
      <figure class="img-border featured-image">
        <img src="https://9to5mac.com/wp-content/uploads/sites/6/2026/11/AI-Apple-2.jpg?w=1600" alt="Featured duplicate" />
      </figure>
      <p class="wp-block-paragraph">Apple @ Work is exclusively brought to you by Mosyle, the only Apple Unified Platform for enterprise devices.</p>
      <p class="wp-block-paragraph">Mount Thor, a Bay Area startup building cloud infrastructure on Apple silicon, announced today that it raised $45 million in fresh funding.</p>
      <p class="wp-block-paragraph">About Apple @ Work: Bradley Chambers managed an enterprise IT network from 2009 to 2021.</p>
      <figure class="wp-block-image">
        <img src="https://9to5mac.com/wp-content/uploads/sites/6/2024/01/mosyle-banner-2024.png?w=1024" alt="Mosyle sponsor" />
      </figure>
      <figure class="wp-block-embed is-type-video is-provider-youtube">
        <iframe data-src="https://www.youtube.com/embed/C1zYX5jwqq4?feature=oembed" title="Demo Video"></iframe>
      </figure>
      <figure class="wp-block-embed is-type-rich is-provider-x">
        <blockquote class="twitter-tweet"><p>GPT-6.2 Astra and Sol are now available for everyone. <a href="https://t.co/abc">https://t.co/abc</a> pic.twitter.com/xyz</p>— OpenAI (@OpenAI) <a href="https://x.com/OpenAI/status/2122750124543926515">November 17, 2026</a></blockquote>
      </figure>
      <blockquote class="wp-block-quote">
        <p>“Making Apple’s operating system and silicon available at datacenter-scale is a massive untapped opportunity for AI workloads.”</p>
      </blockquote>
      <h2 class="wp-block-heading">Wrap up</h2>
      <p class="wp-block-paragraph">The company says the funding will go toward expanding its compute footprint, deploying additional Mac Studio racks across colocation facilities, and building out its engineering team to support autonomous AI agents.</p>
      <p>Do more with your Apple products</p>
      <ul><li>AirPods 5 | Apple’s newest wireless headphones</li></ul>
      <div class="ad-disclaimer-container">FTC: We use income earning auto affiliate links. More.</div>
    </div>
  </article>
</body>
</html>
"""


class TestNineTo5MacCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_nineto5mac_url("https://9to5mac.com/2026/11/17/openai-upgrades-chatgpt/"))
        self.assertFalse(is_nineto5mac_url("https://www.ifixit.com/News/120317/homeview-teardown"))

    def test_sponsor_strip_blockquote_and_youtube(self):
        res = crawl_nineto5mac(
            "https://9to5mac.com/2026/11/12/mount-thor-raises-45-million/",
            html_text=SAMPLE_N95M_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Bradley C")
        self.assertIn("### Wrap up", res["full_text"])
        self.assertIn("massive untapped opportunity", res["full_text"])
        self.assertIn("GPT-6.2 Astra and Sol are now available for everyone.", res["full_text"])
        self.assertIn("OpenAI (@OpenAI)", res["full_text"])
        self.assertNotIn("https://t.co/", res["full_text"])
        # Zero sponsor text, zero About bio, zero FTC disclaimer, zero Mosyle banner
        self.assertNotIn("Mosyle", res["full_text"])
        self.assertNotIn("About Apple @ Work", res["full_text"])
        self.assertNotIn("FTC:", res["full_text"])
        self.assertNotIn("Do more with your Apple", res["full_text"])
        self.assertNotIn("AirPods 5", res["full_text"])
        self.assertEqual(len(res["inline_images"]), 0)
        # YouTube video extracted at exact DOM slot
        self.assertTrue(res["has_video"])
        self.assertEqual(len(res["inline_videos"]), 1)
        self.assertEqual(res["inline_videos"][0]["video_id"], "C1zYX5jwqq4")
        self.assertEqual(res["inline_videos"][0]["after_para"], 0)


if __name__ == "__main__":
    unittest.main()
