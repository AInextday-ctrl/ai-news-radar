#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.siliconangle_crawler import is_siliconangle_url, crawl_siliconangle


class TestSiliconAngleCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_siliconangle_url("https://siliconangle.com/2026/11/17/lancedb-raises-57-5m/"))
        self.assertFalse(is_siliconangle_url("https://openai.com/index/introducing-gpt-6-2/"))

    def test_wp_post_subheadings_cover_and_tail_boilerplate_stop(self):
        wp_post = {
            "id": 77101,
            "date_gmt": "2026-11-17T18:00:00",
            "class_list": ["type-post", "category-ai"],
            "title": {"rendered": "LanceDB raises $57.5M to accelerate AI model training"},
            "_embedded": {
                "author": [{"name": "Kyt Dotson"}],
                "wp:featuredmedia": [{"source_url": "https://images.siliconangle.com/blogs.dir/1/files/2021/11/hand-data-globe.jpg"}],
            },
            "content": {
                "rendered": """
                <p>Multimodal AI data startup LanceDB Inc. announced today that it has raised $57.5 million in new venture funding to expand its open-source vector and multimodal database platform.</p>
                <h3>The challenge of multimodal data for AI</h3>
                <p>Modern AI training pipelines combine video frames, audio transcripts, PDFs, and structured embeddings at petabyte scale, making conventional warehouse replication prohibitively slow.</p>
                <p>LanceDB intends to use the new funding to scale its enterprise lakehouse engine and accelerate frontier model development across customers such as Runway AI.</p>
                <p>Support our mission to keep content open and free by engaging with theCUBE community. Join theCUBE’s Alumni Trust Network today.</p>
                <h3>Are you an AWS customer? Support SiliconANGLE financially by buying your AWS services from our Marketplace portal page.</h3>
                <p>Founded by tech visionaries John Furrier and Dave Vellante, SiliconANGLE Media has built a dynamic ecosystem of industry coverage.</p>
                """
            },
        }
        res = crawl_siliconangle(
            "https://siliconangle.com/2026/11/17/lancedb-raises-57-5m/",
            wp_post=wp_post,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Kyt Dotson")
        self.assertEqual(res["cover_image"], "https://images.siliconangle.com/blogs.dir/1/files/2021/11/hand-data-globe.jpg")
        self.assertIn("### The challenge of multimodal data for AI", res["paragraphs"])
        # Tail donation / AWS Marketplace / founder bio stripped completely
        self.assertNotIn("theCUBE", res["full_text"])
        self.assertNotIn("AWS customer", res["full_text"])
        self.assertNotIn("John Furrier", res["full_text"])


if __name__ == "__main__":
    unittest.main()
