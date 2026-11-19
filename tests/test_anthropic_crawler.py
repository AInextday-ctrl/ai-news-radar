#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for isolated Anthropic dedicated crawler (`crawlers/anthropic_crawler.py`).
"""

import unittest
from crawlers.anthropic_crawler import is_anthropic_url, extract_anthropic_article


SAMPLE_ANTHROPIC_HTML = """<!doctype html>
<html>
<head>
  <title>Progress on provable inference for large language models — Anthropic</title>
  <meta property="og:title" content="Progress on provable inference for large language models — Anthropic" />
  <meta property="og:description" content="Sharing progress on a powerful type of cryptographic proof known as a zkSNARK, uniquely fit for provable inference." />
  <meta property="og:image" content="https://assets.claude.com/66a72ed558145b284fcefd6c2e279eae2e134bc0.jpg" />
  <meta property="article:published_time" content="2026-11-02T00:00:00.000Z" />
</head>
<body>
  <article class="EaEYjq_Article">
    <header class="VYxBBq_Header">
      <h1 class="VYxBBq_Title">Progress on provable inference for large language models</h1>
      <div class="fKLU0a_item">PublishedNov 2, 2026</div>
      <time>Nov 2, 2026</time>
      <div class="fKLU0a_item">TeamFrontier Red Team</div>
    </header>
    <div class="EaEYjq_ContentWrapper">
      <div class="PA4F1q_body">
        <p>In this post, we share our early progress on applying zero-knowledge proofs to machine learning models.</p>
        <h2>01Executive summary</h2>
        <p>Zero-knowledge proofs allow a prover to convince a verifier that a statement is true without revealing secret inputs.</p>
        <ul>
          <li>First, provable inference establishes that a specific model produced an exact output.</li>
          <li>Second, cryptographic commitments prevent unauthorized tampering during execution.</li>
        </ul>
        <h3>Challenge 1: computational pacing</h3>
        <p>The primary hurdle remains the large overhead of translating tensor operations into arithmetic circuits.</p>
        <figure class="qJNyFq_post-video-container">
          <video src="https://assets.claude.com/test_demo.mp4"></video>
          <figcaption>Demonstration of zero-knowledge circuit synthesis.</figcaption>
        </figure>
        <p>Recent advances in polynomial commitment schemes have reduced this latency by nearly an order of magnitude.</p>
        <figure class="Duq99q_e-imageWithCaption">
          <img src="https://assets.claude.com/benchmark_chart.png" alt="Latency reduction chart across model sizes." />
          <figcaption>Latency reduction across various circuit topologies.</figcaption>
        </figure>
        <p>We are making this benchmark suite publicly available to help accelerate academic and industrial research.</p>
        <div class="EaEYjq_ConstellationPanelSlot">
          <p>Related articles</p>
          <p>Updating our coordinated vulnerability disclosure policy timelines</p>
        </div>
      </div>
    </div>
  </article>
</body>
</html>
"""


class TestAnthropicCrawler(unittest.TestCase):
    def test_url_matching(self):
        self.assertTrue(is_anthropic_url("https://www.anthropic.com/research/provable-inference"))
        self.assertTrue(is_anthropic_url("https://anthropic.com/news/roadshow-launch"))
        self.assertTrue(is_anthropic_url("https://claude.com/blog/duet"))
        self.assertTrue(is_anthropic_url("https://docs.anthropic.com/en/docs/overview"))
        self.assertFalse(is_anthropic_url("https://www.google.com/search?q=anthropic"))
        self.assertFalse(is_anthropic_url("https://open-anthropic.org/news"))
        self.assertFalse(is_anthropic_url(""))

    def test_article_extraction(self):
        res = extract_anthropic_article(
            "https://www.anthropic.com/research/provable-inference",
            use_cache=False,
            localize_cover=False,
            html_text=SAMPLE_ANTHROPIC_HTML,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_substantive"])
        self.assertEqual(res["title"], "Progress on provable inference for large language models")
        self.assertEqual(res["author"], "Frontier Red Team")
        self.assertEqual(res["published_at"], "Nov 2, 2026")
        self.assertIn("zkSNARK", res["summary"])
        self.assertIn("### Executive summary", res["paragraphs"])
        self.assertNotIn("### 01Executive summary", res["paragraphs"])
        self.assertIn("#### Challenge 1: computational pacing", res["paragraphs"])
        self.assertTrue(any(p.startswith("• First, provable inference") for p in res["paragraphs"]))
        # Video extraction
        self.assertEqual(len(res["inline_videos"]), 1)
        self.assertEqual(res["inline_videos"][0]["url"], "https://assets.claude.com/test_demo.mp4")
        self.assertEqual(res["inline_videos"][0]["title"], "Demonstration of zero-knowledge circuit synthesis.")
        # Image extraction
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertEqual(res["inline_images"][0]["url"], "https://assets.claude.com/benchmark_chart.png")
        self.assertEqual(res["inline_images"][0]["caption_en"], "Latency reduction across various circuit topologies.")
        # Hard stop / sidebar exclusion
        self.assertNotIn("Related articles", res["full_text"])


if __name__ == "__main__":
    unittest.main()
