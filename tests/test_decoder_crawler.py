#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.decoder_crawler import is_decoder_url, crawl_decoder


class TestDecoderCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_decoder_url("https://the-decoder.com/openai-launches-gpt-6-2-astra-and-sol/"))
        self.assertFalse(is_decoder_url("https://www.cnbc.com/2026/11/17/test.html"))

    def test_wp_post_subheadings_benchmark_charts_and_promo_strip(self):
        wp_post = {
            "id": 99123,
            "date_gmt": "2026-11-17T14:00:00",
            "class_list": ["type-post", "category-ai"],
            "title": {"rendered": "OpenAI launches GPT-6.2 Astra and Sol with lower API prices"},
            "jetpack_featured_media_url": "http://the-decoder.com/wp-content/uploads/2026/11/openai_vals_sol.png",
            "_embedded": {"author": [{"name": "Matthias Bastian"}]},
            "content": {
                "rendered": """
                <h2>Key Points</h2>
                <p>OpenAI has introduced GPT-6.2 Astra and its smaller sibling Sol, targeting frontier scientific reasoning and dramatically lower inference costs across enterprise APIs.</p>
                <h2>Benchmark performance across coding and science</h2>
                <figure><img src="http://the-decoder.com/wp-content/uploads/2026/11/FrontierCode-2.0.png"/><figcaption>GPT-6.2 Astra leads on FrontierCode 2.0.</figcaption></figure>
                <p>Independent evaluators including Epoch AI and Artificial Analysis report strong gains on long-horizon coding benchmarks while noting remaining variance on real-world legal tasks.</p>
                <iframe src="https://www.youtube.com/embed/C1zYX5jwqq4?feature=oembed"></iframe>
                <p>Pricing for Sol drops well below prior flagship tiers, intensifying margin pressure across rival foundation model providers.</p>
                <p>Subscribe to THE DECODER for ad-free reading, a weekly AI newsletter, and our exclusive front page.</p>
                """
            },
        }
        res = crawl_decoder(
            "https://the-decoder.com/openai-launches-gpt-6-2-astra-and-sol/",
            wp_post=wp_post,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Matthias Bastian")
        # http:// upgraded to https://
        self.assertTrue(res["cover_image"].startswith("https://"))
        # Key Points heading skipped; real subheading kept inline as `### `
        self.assertNotIn("### Key Points", res["paragraphs"])
        self.assertIn("### Benchmark performance across coding and science", res["paragraphs"])
        # Promo stripped
        self.assertNotIn("ad-free reading", res["full_text"])
        # Benchmark chart preserved with exact `after_para` anchor & https URL
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertTrue(res["inline_images"][0]["url"].startswith("https://"))
        self.assertEqual(res["inline_images"][0]["after_para"], 1)
        # YouTube video extracted
        self.assertTrue(res["has_video"])
        self.assertEqual(res["video_id"], "C1zYX5jwqq4")

    def test_video_cover_fallback_editorial_logo_and_two_para_brief(self):
        from crawlers.decoder_crawler import _is_valid_decoder_image
        self.assertTrue(_is_valid_decoder_image("https://the-decoder.com/wp-content/uploads/2026/11/nvidia_logo_glitch.png"))
        self.assertFalse(_is_valid_decoder_image("https://the-decoder.com/wp-content/uploads/2026/11/Qwen_small_480p.mp4"))
        self.assertFalse(_is_valid_decoder_image("https://the-decoder.com/wp-content/uploads/2026/11/Banner_The-Decoder_SoMe.png"))
        self.assertFalse(_is_valid_decoder_image("https://the-decoder.com/wp-content/uploads/decoder-logo.png"))

        wp_post = {
            "id": 99124,
            "class_list": ["type-post"],
            "title": {"rendered": "Google's Gemini 4 Carbon tops MathArena benchmark"},
            "jetpack_featured_media_url": "https://the-decoder.com/wp-content/uploads/2026/11/demo_clip_480p.mp4",
            "_embedded": {"author": [{"name": "Matthias Bastian"}]},
            "content": {
                "rendered": """
                <p>Google's Gemini 4 Carbon has become the first non-OpenAI model in a while to top the MathArena math benchmark, knocking GPT-6.1 Sol from the top spot while Claude Fable 5.2 came in second across demanding olympiad tasks.</p>
                <figure><img src="https://the-decoder.com/wp-content/uploads/2026/11/matharena_chart.png"/><figcaption>MathArena benchmark results.</figcaption></figure>
                <p>With the highest reasoning settings enabled during evaluation, Gemini 4 Carbon and Claude Fable 5.2 cost roughly 15 and 40 times as much per problem as GPT-6.1 Sol, respectively, highlighting a sharp inference-cost trade-off.</p>
                """
            },
        }
        res = crawl_decoder(
            "https://the-decoder.com/gemini-4-carbon-takes-the-matharena-crown/",
            wp_post=wp_post,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_substantive"])
        self.assertEqual(res["cover_image"], "https://the-decoder.com/wp-content/uploads/2026/11/matharena_chart.png")
        self.assertEqual(len(res["inline_images"]), 0)


if __name__ == "__main__":
    unittest.main()
