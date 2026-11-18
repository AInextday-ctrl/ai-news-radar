#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.cnbc_crawler import is_cnbc_url, crawl_cnbc, _cnbc_media_stem


class TestCnbcCrawler(unittest.TestCase):
    def test_url_and_asset_stem(self):
        self.assertTrue(is_cnbc_url("https://www.cnbc.com/2026/11/17/nvidia-jensen-huang-house-committee.html"))
        self.assertFalse(is_cnbc_url("https://arstechnica.com/gadgets/2026/11/test/"))
        self.assertEqual(
            _cnbc_media_stem("https://image.cnbcfm.com/api/v1/image/108553117-foo.jpeg?w=750"),
            _cnbc_media_stem("https://image.cnbcfm.com/api/v1/image/108553117-foo.jpeg?w=1920&h=1080"),
        )

    def test_article_body_video_and_promo_stripping(self):
        sample_html = """
        <html><head>
        <script type="application/ld+json">
        {
          "@type": "NewsArticle",
          "headline": "Jensen Huang slated to appear before House panels Dec. 1; Nvidia lawyer due to testify Dec. 2",
          "author": [{"@type": "Person", "name": "Garrett Downs"}, {"@type": "Person", "name": "Megan Cassella"}],
          "datePublished": "2026-11-17T21:00:00Z",
          "image": [
            {"@type": "ImageObject", "url": "https://image.cnbcfm.com/api/v1/image/108553117-hero.jpeg?w=1920&h=1080", "width": 1920, "height": 1080},
            {"@type": "ImageObject", "url": "https://image.cnbcfm.com/api/v1/image/108553117-hero.jpeg?w=1200&h=1200", "width": 1200, "height": 1200}
          ],
          "video": {
            "@type": "VideoObject",
            "contentUrl": "https://pdl-iphone-cnbc-com.akamaized.net/7000431430/clip-hd_L.mp4",
            "name": "Jensen Huang to appear before House Foreign Affairs panel Dec. 1",
            "thumbnailUrl": "https://image.cnbcfm.com/api/v1/image/108553117-hero.jpeg?w=750&h=422"
          }
        }
        </script>
        </head><body>
        <h1 class="ArticleHeader-headline">Jensen Huang slated to appear before House panels Dec. 1; Nvidia lawyer due to testify Dec. 2</h1>
        <div class="ArticleBody-articleBody">
          <div class="RelatedQuotes-relatedQuotes"><p>NVDA stock ticker widget noise</p></div>
          <div class="group">
            <p>Former Nvidia CEO Jensen Huang will appear before the House Foreign Affairs, Intelligence and China Select committees on Dec. 1 for a transcribed interview regarding export controls.</p>
            <figure><img src="https://image.cnbcfm.com/api/v1/image/108553117-hero.jpeg?w=750&h=422"/></figure>
            <h2>Congressional scrutiny intensifies</h2>
            <p>Nvidia general counsel Tim Teter is also scheduled to testify before the panels on Dec. 2, lawmakers confirmed in a joint statement released Tuesday afternoon.</p>
            <p>Lawmakers are examining how advanced AI accelerators reached overseas data centers serving restricted entities despite tightening U.S. export rules.</p>
            <h2>Read more CNBC news on Nvidia</h2>
            <p>Subscribe to CNBC PRO to unlock exclusive Wall Street insights.</p>
          </div>
        </div>
        </body></html>
        """
        res = crawl_cnbc(
            "https://www.cnbc.com/2026/11/17/nvidia-jensen-huang-house-committee.html",
            title="Jensen Huang will appear before the House (CNBC)",
            html_text=sample_html,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Jensen Huang slated to appear before House panels Dec. 1; Nvidia lawyer due to testify Dec. 2")
        self.assertEqual(res["author"], "Garrett Downs and Megan Cassella")
        # Direct HD MP4 broadcast video extracted
        self.assertTrue(res["has_video"])
        self.assertEqual(res["video_provider"], "mp4")
        self.assertIn("akamaized.net", res["video_url"])
        # Real subheading kept inline; "Read more CNBC" and "CNBC PRO" and ticker widget stripped
        self.assertIn("### Congressional scrutiny intensifies", res["paragraphs"])
        self.assertNotIn("Read more CNBC", res["full_text"])
        self.assertNotIn("CNBC PRO", res["full_text"])
        self.assertNotIn("NVDA stock ticker", res["full_text"])
        # Same-ID cover photo deduplicated
        self.assertEqual(res["inline_images"], [])


if __name__ == "__main__":
    unittest.main()
