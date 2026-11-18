#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.tomshardware_crawler import crawl_tomshardware, is_tomshardware_url


SAMPLE_TOMS_HTML = """<!doctype html>
<html>
<head>
  <meta property="og:title" content="Nvidia announces Rubin HPC GPU - Tom's Hardware" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Nvidia announces Rubin HPC GPU with record CUDA cores",
    "datePublished": "2026-11-16T19:05:24+00:00",
    "author": {"@type": "Person", "name": "Jeffrey Kampman"},
    "image": [{"@type": "ImageObject", "url": "https://cdn.mos.cms.futurecdn.net/wJ2qnaAhPDGJQVsKBgLAri-1920-80.png"}]
  }
  </script>
</head>
<body>
  <article>
    <div id="article-body" class="text-copy bodyCopy auto paywall-locker">
      <p>The Supercomputing 2026 conference is under way, and Nvidia announced the Rubin HPC GPU targeting large-scale scientific workloads.</p>
      <p class="kiosq-b">Today's Rubin GPU has 224 SMs and 28,672 CUDA cores, while the new Rubin HPC scales compute resources with NVLink 7 interconnect.</p>
      <div class="slice-container table-wrapper slice-container-table kiosq-b">
        <p>Swipe to scroll horizontally</p>
        <table>
          <tr><th>Date</th><th>Who</th><th>Claim</th></tr>
          <tr><td>Nov. 10, 2026</td><td>Tom Brown</td><td>Mythos ported almost 100% of kernels in three days</td></tr>
        </table>
      </div>
      <figure class="van-image-figure inline-layout kiosq-b">
        <img src="https://cdn.mos.cms.futurecdn.net/wJ2qnaAhPDGJQVsKBgLAri-650-80.png" alt="Duplicate cover resized" />
      </figure>
      <figure class="van-image-figure inline-layout kiosq-b">
        <img src="https://cdn.mos.cms.futurecdn.net/qkDmAUP4gEEK88Sc6vyaQV-650-80.jpg" data-original-mos="https://cdn.mos.cms.futurecdn.net/qkDmAUP4gEEK88Sc6vyaQV.jpg" alt="Anthropic slide" />
        <figcaption>(Image credit: Anthropic)</figcaption>
      </figure>
      <div class="hawk-widget"><p>Today's best GPU deals at Amazon</p></div>
      <p class="kiosq-b">Nvidia says Rubin HPC will arrive sometime in 2028 for climate research, genomic analysis, and financial simulation workloads.</p>
      <p>Follow Tom's Hardware on Google News to get our latest reviews and benchmarks.</p>
    </div>
  </article>
</body>
</html>
"""


class TestTomsHardwareCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_tomshardware_url("https://www.tomshardware.com/pc-components/gpus/nvidia-rubin-hpc"))
        self.assertFalse(is_tomshardware_url("https://9to5mac.com/2026/11/17/openai"))

    def test_kiosq_tables_futurecdn_dedup_and_promo_strip(self):
        res = crawl_tomshardware(
            "https://www.tomshardware.com/pc-components/gpus/nvidia-rubin-hpc",
            html_text=SAMPLE_TOMS_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Jeffrey Kampman")
        self.assertIn("NVLink 7 interconnect", res["full_text"])
        self.assertIn("• Date: Nov. 10, 2026 | Who: Tom Brown | Claim: Mythos ported almost 100% of kernels in three days", res["full_text"])
        self.assertNotIn("Swipe to scroll horizontally", res["full_text"])
        self.assertNotIn("Today's best GPU deals", res["full_text"])
        self.assertNotIn("Follow Tom's Hardware on Google News", res["full_text"])
        # Duplicate Future CDN -650-80 cover stripped; HD data-original-mos inline kept
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertEqual(res["inline_images"][0]["url"], "https://cdn.mos.cms.futurecdn.net/qkDmAUP4gEEK88Sc6vyaQV.jpg")
        self.assertEqual(res["inline_images"][0]["after_para"], 2)


if __name__ == "__main__":
    unittest.main()
