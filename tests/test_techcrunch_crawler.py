#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.techcrunch_crawler import (
    is_techcrunch_url,
    crawl_techcrunch,
    _extract_tc_slug,
)


class TestTechCrunchCrawler(unittest.TestCase):
    def test_url_and_slug_detection(self):
        u = "https://techcrunch.com/2026/11/17/nvidia-is-abandoning-china-after-jensen-huangs-ouster/"
        self.assertTrue(is_techcrunch_url(u))
        self.assertEqual(_extract_tc_slug(u), "nvidia-is-abandoning-china-after-jensen-huangs-ouster")
        self.assertFalse(is_techcrunch_url("https://www.wired.com/story/test/"))

    def test_wp_post_extraction_promo_stripping_and_dedup(self):
        wp_post = {
            "id": 3100001,
            "date_gmt": "2026-11-17T20:00:00",
            "class_list": ["type-post", "category-artificial-intelligence", "tag-nvidia"],
            "title": {"rendered": "Nvidia is abandoning China after Jensen Huang&#8217;s ouster"},
            "excerpt": {"rendered": "<p>Acting CEO Colette Kress said Nvidia will no longer sell H200 chips in China.</p>"},
            "jetpack_featured_media_url": "https://techcrunch.com/wp-content/uploads/2026/03/jensen-hero.jpg?w=1200",
            "_embedded": {"author": [{"name": "Tim Fernholz"}]},
            "content": {
                "rendered": """
                <p>Nvidia will no longer sell its H200 chips in China, acting CEO Colette Kress said Tuesday , ending the company&#8217;s participation in a controversial loophole.</p>
                <div class="jw-player-inline-promo wp-block-techcrunch-jw-player-embed"><p>Watch TechCrunch Disrupt 2026 highlights</p><iframe src="https://cdn.jwplayer.com/players/fake.html"></iframe></div>
                <p>China&#8217;s access to leading AI accelerators was an important topic during the company&#8217;s first earnings call since Jensen Huang stepped down last week .</p>
                <figure class="wp-block-image"><img src="https://techcrunch.com/wp-content/uploads/2026/03/jensen-hero-1024x576.jpg?w=1024"/><figcaption class="wp-block-image__credits">Image Credits: Getty Images</figcaption></figure>
                <figure class="wp-block-image"><img src="https://techcrunch.com/wp-content/uploads/2026/11/chip-export-chart.png?w=900"/></figure>
                <p>Export control attorneys say data centers outside China will also have to certify they are not serving Chinese AI labs under the updated compliance rules.</p>
                <p>Join the Disrupt 2026 waitlist now to save on early-bird passes.</p>
                """
            },
        }
        res = crawl_techcrunch(
            "https://techcrunch.com/2026/11/17/nvidia-is-abandoning-china-after-jensen-huangs-ouster/",
            title="Colette Kress says Nvidia will no longer sell H200 chips in China (TechCrunch)",
            wp_post=wp_post,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["is_filtered_out"])
        self.assertEqual(res["title"], "Nvidia is abandoning China after Jensen Huang’s ouster")
        self.assertEqual(res["author"], "Tim Fernholz")
        self.assertEqual(res["paras_count"], 3)
        # Punctuation spacing artifact fixed ("Tuesday ," -> "Tuesday,")
        self.assertIn("Tuesday, ending", res["full_text"])
        self.assertIn("last week.", res["full_text"])
        # Promo & Disrupt blocks stripped
        self.assertNotIn("Disrupt 2026", res["full_text"])
        self.assertNotIn("Image Credits", res["full_text"])
        self.assertFalse(res["has_video"])
        # Cover image deduplicated, genuine inline chart preserved
        self.assertEqual(
            res["inline_images"],
            ["https://techcrunch.com/wp-content/uploads/2026/11/chip-export-chart.png"],
        )

    def test_rejects_sponsored_and_roundup(self):
        res = crawl_techcrunch(
            "https://techcrunch.com/2026/11/17/sponsored-ai-cloud-partner/",
            wp_post={
                "id": 3100002,
                "class_list": ["type-post", "tag-sponsored"],
                "title": {"rendered": "How CloudCorp accelerates enterprise AI"},
                "content": {"rendered": "<p>Partner content produced by CloudCorp.</p>"},
            },
            localize_cover=False,
            use_cache=False,
        )
        self.assertTrue(res["is_filtered_out"])
        self.assertEqual(res["status"], "filtered_promo_or_roundup")


if __name__ == "__main__":
    unittest.main()
