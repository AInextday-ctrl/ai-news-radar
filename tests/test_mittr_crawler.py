#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.mittr_crawler import (
    is_mittr_url,
    crawl_mittr,
    _extract_mittr_post_id,
    _mittr_media_stem,
)


class TestMittrCrawler(unittest.TestCase):
    def test_url_and_post_id_detection(self):
        u = "https://www.technologyreview.com/2026/11/16/1148624/the-open-source-movement-wants-jensen-huang-back/"
        self.assertTrue(is_mittr_url(u))
        self.assertEqual(_extract_mittr_post_id(u), "1148624")
        self.assertFalse(is_mittr_url("https://www.wired.com/story/test/"))

    def test_wp_post_extraction_noise_filtering_and_audio_exclusion(self):
        wp_post = {
            "id": 1148624,
            "date_gmt": "2026-11-16T12:00:00",
            "title": {"rendered": "The open-source movement wants Jensen Huang back &#8211; MIT Technology Review"},
            "excerpt": {"rendered": "<p>Open-source AI builders rally behind Nvidia&#8217;s former chief.</p>"},
            "jetpack_featured_media_url": "https://wp.technologyreview.com/wp-content/uploads/2026/11/hero-photo.jpg",
            "_embedded": {"author": [{"name": "James Donnell"}]},
            "content": {
                "rendered": """
                <p>A petition to reinstate Jensen Huang as Nvidia CEO has attracted more than 115,000 signatures from across the global AI ecosystem, with open-source researchers making up a surprising share of the supporters.</p>
                <p>Many open-source developers argue that Huang consistently championed CUDA accessibility and academic research grants even while building a proprietary hardware empire.</p>
                <p>Sign up for The Download to get your daily dose of what's going on in the world of technology.</p>
                <figure><img src="https://wp.technologyreview.com/wp-content/uploads/2026/11/hero-photo-1024x576.jpg?resize=1024,576"/></figure>
                <figure><img src="https://wp.technologyreview.com/wp-content/uploads/2026/11/inline-chart.png?w=1200"/></figure>
                <iframe src="https://player.simplecast.com/6bc0fc65-c367-4512-8241-ce7400c67e9f?dark=false"></iframe>
                <p>Industry observers say the petition reflects anxiety over whether Nvidia's next leadership team will preserve the company's deep ties with open-weight model communities.</p>
                <p>Related Stories:</p>
                <p>This content was produced by Partner Corp. It was not written by MIT Technology Review’s editorial staff.</p>
                """
            },
        }
        res = crawl_mittr(
            "https://www.technologyreview.com/2026/11/16/1148624/the-open-source-movement-wants-jensen-huang-back/",
            wp_post=wp_post,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertEqual(res["title"], "The open-source movement wants Jensen Huang back")
        self.assertEqual(res["author"], "James Donnell")
        self.assertEqual(res["paras_count"], 3)
        self.assertNotIn("Sign up for The Download", res["full_text"])
        self.assertNotIn("Related Stories", res["full_text"])
        self.assertNotIn("not written by MIT Technology Review", res["full_text"])
        # Simplecast audio iframe must NOT be marked as video
        self.assertFalse(res["has_video"])
        # Cover stem duplicate removed; genuine inline chart preserved
        self.assertEqual(
            res["inline_images"],
            ["https://wp.technologyreview.com/wp-content/uploads/2026/11/inline-chart.png"],
        )

    def test_vimeo_video_and_html_author_fallback(self):
        wp_post = {
            "id": 1148049,
            "title": {"rendered": "Roundtables: Inside the Quest for Cognitive Immortality"},
            "jetpack_featured_media_url": "",
            "_embedded": {},
            "content": {
                "rendered": """
                <p>Listen to the session or watch below</p>
                <p>In an effort to reach an elusive continuity of the self, some far-thinking technologists are working on ways to keep your brain going—even beyond death. Science editor Mary Beth Griggs and senior editor Antonio Regalado explore gradual brain replacement and uploading memories to the cloud.</p>
                <iframe src="https://player.vimeo.com/video/1247719173?dnt=1&amp;app_id=122963"></iframe>
                """
            },
        }
        html_sample = """
        <html><head>
        <meta property="og:image" content="https://wp.technologyreview.com/wp-content/uploads/2026/11/roundtable.png?resize=1200,600"/>
        </head><body>
        <div class="byline__wrapper"><a href="/author/antonio-regalado/">Antonio Regalado<span>archive page</span></a></div>
        <aside class="related-stories"><a href="/author/will-douglas-heaven/">Will Douglas Heaven<span>archive page</span></a></aside>
        </body></html>
        """
        res = crawl_mittr(
            "https://www.technologyreview.com/2026/11/17/1148049/roundtables-inside-the-quest-for-cognitive-immortality/",
            wp_post=wp_post,
            html_text=html_sample,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_video"])
        self.assertEqual(res["video_id"], "1247719173")
        self.assertEqual(res["author"], "Antonio Regalado")
        self.assertEqual(
            res["cover_image"],
            "https://wp.technologyreview.com/wp-content/uploads/2026/11/roundtable.png",
        )


if __name__ == "__main__":
    unittest.main()
