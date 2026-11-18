#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.arstechnica_crawler import is_arstechnica_url, crawl_arstechnica


class TestArsTechnicaCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_arstechnica_url("https://arstechnica.com/gadgets/2026/11/microsoft-calls-copilot-the-new-os-for-work-at-ignite-keynote/"))
        self.assertFalse(is_arstechnica_url("https://techcrunch.com/2026/11/17/test/"))

    def test_multi_block_post_content_and_figure_dedup(self):
        sample_html = """
        <html>
        <head>
          <meta property="og:image" content="https://cdn.arstechnica.net/wp-content/uploads/2026/11/hero-ignite.jpg?resize=1200,630" />
          <script type="application/ld+json">
          {"@type": "NewsArticle", "headline": "Copilot is “the new OS for work,” and now Office runs inside of it", "author": {"@type": "Person", "name": "Nick Indge"}, "datePublished": "2026-11-17T18:00:00Z"}
          </script>
        </head>
        <body>
          <h1>Copilot is “the new OS for work,” and now Office runs inside of it</h1>
          <div class="post-content post-content-double">
            <p>Opening the keynote at its Ignite event, Microsoft CEO Satya Nadella outlined the company’s vision for Copilot as the central workspace where Word, Excel, and PowerPoint run natively.</p>
            <figure>
              <img src="https://cdn.arstechnica.net/wp-content/uploads/2026/11/hero-ignite-1152x648.jpg" />
              <figcaption>Enlarge / Hero duplicate</figcaption>
            </figure>
            <h2>All about agents</h2>
            <p>The announcement marks a striking inversion of how enterprise software has worked for decades, placing conversational AI agents ahead of traditional desktop windows.</p>
          </div>
          <div class="ad-slot"><p>Sponsored ad slot that must never appear in editorial paragraphs.</p></div>
          <div class="post-content post-content-double">
            <h2>The outage in the room</h2>
            <p>Nadella also addressed last week’s enterprise cloud outage while introducing Microsoft IQ as an intelligence orchestration layer across corporate tenants.</p>
            <figure>
              <img src="https://cdn.arstechnica.net/wp-content/uploads/2026/11/MS_New_Ecosystem_Stack_AI.jpg" />
              <figcaption>Enlarge / Microsoft's new Ignite AI ecosystem stack.</figcaption>
            </figure>
            <p>When you purchase through links in our articles, we may earn a small commission.</p>
          </div>
        </body>
        </html>
        """
        res = crawl_arstechnica(
            "https://arstechnica.com/gadgets/2026/11/microsoft-calls-copilot-the-new-os-for-work-at-ignite-keynote/",
            title="Microsoft makes Word, Excel, and PowerPoint generally available (Ars Technica)",
            html_text=sample_html,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Copilot is “the new OS for work,” and now Office runs inside of it")
        self.assertEqual(res["author"], "Nick Indge")
        # Both .post-content blocks aggregated with inline subheadings (`### `) preserved in exact order
        self.assertEqual(res["paras_count"], 5)
        self.assertIn("### All about agents", res["paragraphs"])
        self.assertIn("### The outage in the room", res["paragraphs"])
        self.assertNotIn("Sponsored ad slot", res["full_text"])
        self.assertNotIn("earn a small commission", res["full_text"])
        # Hero cover deduplicated; authentic figure kept with `Enlarge /` stripped and exact `after_para` anchor
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertEqual(res["inline_images"][0]["url"], "https://cdn.arstechnica.net/wp-content/uploads/2026/11/MS_New_Ecosystem_Stack_AI.jpg")
        self.assertEqual(res["inline_images"][0]["caption"], "Microsoft's new Ignite AI ecosystem stack.")
        self.assertEqual(res["inline_images"][0]["after_para"], 4)


if __name__ == "__main__":
    unittest.main()
