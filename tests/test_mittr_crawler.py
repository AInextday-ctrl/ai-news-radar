#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.mittr_crawler import (
    is_mittr_url,
    crawl_mittr,
    _extract_mittr_post_id,
)
from crawlers.content_filters import is_low_value_roundup_or_promo


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
            "class_list": ["type-post", "category-artificial-intelligence", "tag-the-algorithm"],
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
        self.assertFalse(res["is_filtered_out"])
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertEqual(res["title"], "The open-source movement wants Jensen Huang back")
        self.assertEqual(res["author"], "James Donnell")
        self.assertEqual(res["paras_count"], 3)
        self.assertNotIn("Sign up for The Download", res["full_text"])
        self.assertNotIn("Related Stories", res["full_text"])
        # Simplecast audio iframe must NOT be marked as video
        self.assertFalse(res["has_video"])
        # Cover stem duplicate removed; genuine inline chart preserved
        self.assertEqual(
            res["inline_images"],
            ["https://wp.technologyreview.com/wp-content/uploads/2026/11/inline-chart.png"],
        )

    def test_vimeo_video_and_scoped_html_author_fallback(self):
        wp_post = {
            "id": 1149999,
            "class_list": ["type-post", "category-artificial-intelligence"],
            "title": {"rendered": "Inside the AI Chip Race"},
            "jetpack_featured_media_url": "",
            "_embedded": {},
            "content": {
                "rendered": """
                <p>Chip designers across Silicon Valley and Asia are racing to build next-generation custom silicon optimized for agentic inference workloads and lower datacenter power budgets across hyperscale clusters.</p>
                <p>Engineers interviewed in our video documentary explain how packaging bottlenecks, high-bandwidth memory pricing, and compiler ecosystems are reshaping competition beyond Nvidia's traditional GPU moat.</p>
                <iframe src="https://player.vimeo.com/video/1247719173?dnt=1&amp;app_id=122963"></iframe>
                """
            },
        }
        html_sample = """
        <html><head>
        <meta property="og:image" content="https://wp.technologyreview.com/wp-content/uploads/2026/11/chip-race.png?resize=1200,600"/>
        </head><body>
        <div class="byline__wrapper"><a href="/author/antonio-regalado/">Antonio Regalado<span>archive page</span></a></div>
        <aside class="related-stories"><a href="/author/will-douglas-heaven/">Will Douglas Heaven<span>archive page</span></a></aside>
        </body></html>
        """
        res = crawl_mittr(
            "https://www.technologyreview.com/2026/11/18/1149999/inside-the-ai-chip-race/",
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
            "https://wp.technologyreview.com/wp-content/uploads/2026/11/chip-race.png",
        )

    def test_rejects_roundups_promos_and_sponsored_advertorials(self):
        # 1. The Download link roundup
        r1 = crawl_mittr(
            "https://www.technologyreview.com/2026/11/17/1148679/the-download-jensen-huang-open-source-ai-cognitive-immortality/",
            title="The Download: Jensen Huang’s open-source dilemma and cognitive immortality",
            use_cache=False,
        )
        self.assertTrue(r1["is_filtered_out"])
        self.assertEqual(r1["status"], "filtered_promo_or_roundup")

        # 2. Subscriber hub & Roundtable promo
        r2 = crawl_mittr(
            "https://www.technologyreview.com/2026/11/17/1148203/research-reports/",
            title="Research Reports",
            use_cache=False,
        )
        self.assertTrue(r2["is_filtered_out"])

        r3 = crawl_mittr(
            "https://www.technologyreview.com/2026/11/17/1148049/roundtables-inside-the-quest-for-cognitive-immortality/",
            title="Roundtables: Inside the Quest for Cognitive Immortality",
            use_cache=False,
        )
        self.assertTrue(r3["is_filtered_out"])

        # 3. Innocent-looking title with `tag-sponsored` WP class
        r4 = crawl_mittr(
            "https://www.technologyreview.com/2026/11/16/1148565/building-trustworthy-ai-by-fencing-it-in-not-predicting-it/",
            wp_post={
                "id": 1148565,
                "class_list": ["type-post", "category-artificial-intelligence", "tag-sponsored"],
                "title": {"rendered": "Building trustworthy AI by fencing it in, not predicting it"},
                "content": {"rendered": "<p>This content was produced by UL Solutions. It was not written by MIT Technology Review’s editorial staff.</p>"},
            },
            localize_cover=False,
            use_cache=False,
        )
        self.assertTrue(r4["is_filtered_out"])

        # 4. Multi-outlet link roundup body detector vs single-outlet investigative journalism
        self.assertTrue(
            is_low_value_roundup_or_promo(
                title="Today's Tech Links",
                url="https://example.com/links",
                body="Chip export rules tighten (AP). China may retaliate (Bloomberg $). Nvidia warns customers (CNBC). AI distillation expands (Reuters $).",
            )
        )
        # Genuine Bloomberg original scoop (even under /news/newsletters/) must NOT be filtered
        self.assertFalse(
            is_low_value_roundup_or_promo(
                title="Apple Bets on Siri AI Apps as the Main Draw for Its Smart Glasses",
                url="https://www.bloomberg.com/news/newsletters/2026-11-15/apple-siri-ai-app-integrations",
                body="Apple is preparing a new smart glasses platform (Bloomberg) with Siri AI integrations (Bloomberg) according to people familiar with the matter (Bloomberg).",
            )
        )


if __name__ == "__main__":
    unittest.main()
