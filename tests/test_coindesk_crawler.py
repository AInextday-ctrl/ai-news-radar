#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.coindesk_crawler import crawl_coindesk, is_coindesk_url


SAMPLE_COINDESK_HTML = """<!doctype html>
<html>
<head>
  <meta property="og:title" content="Solana Foundation takes majority stake in CoinGecko | CoinDesk" />
  <meta property="og:image" content="https://cdn.sanity.io/images/s3y3vcno/production/cover-1920x1280.jpg?w=1200&h=675" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Solana Foundation takes majority stake in CoinGecko",
    "abstract": "The foundation plans Solana-powered trading on CoinGecko.",
    "datePublished": "2026-11-17T11:29:51.809Z",
    "author": [
      {"@type": "Person", "name": "Francisco Rodrigues"},
      {"@type": "Person", "name": "Helene Braun"}
    ],
    "image": {
      "@type": "ImageObject",
      "url": "https://cdn.sanity.io/images/s3y3vcno/production/cover-1920x1280.jpg?auto=format&w=1200&h=675"
    }
  }
  </script>
</head>
<body>
  <main>
    <div class="article-content-wrapper">
      <div class="mt-4 mb-8 rounded-[7px] p-[2px]">
        <div class="document-body font-body-lg !font-sans !text-md !leading-6">
          <ul>
            <li>Summary bullet that should not duplicate the article body.</li>
          </ul>
        </div>
      </div>
      <div class="document-body font-body-lg [&_.premium-component]:!hidden">
        <p>The Solana Foundation has taken a majority interest in <a href="https://example.com">CoinGecko</a>, one of the crypto ecosystem’s largest data providers.</p>
        <p>The foundation <a href="https://example.com">said it plans to bring trading</a> to CoinGecko’s website and mobile app for its 18 million users.</p>
        <figure>
          <button type="button" data-image-src="https://cdn.sanity.io/images/s3y3vcno/production/chart-1390x818.png?auto=format">
            <img src="/_next/image?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fs3y3vcno%2Fproduction%2Fchart-1390x818.png&w=1080&q=75" alt="Stablecoin payment volume" />
          </button>
          <figcaption>Enlarge image Stablecoin payment volume jumped 45% this year. (CoinDesk)</figcaption>
        </figure>
        <figure>
          <img src="/_next/image?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fs3y3vcno%2Fproduction%2Fcover-1920x1280.jpg&w=740&q=75" alt="Duplicate cover" />
        </figure>
        <h3>Expanding market infrastructure</h3>
        <p>Read more: Stripe to expand stablecoin cards to over 100 countries</p>
      </div>
    </div>
    <div class="article-content-wrapper">
      <div class="document-body font-body-lg [&_.premium-component]:!hidden">
        <p>CoinGecko also plans to expand coverage of tokenized real-world assets while improving data infrastructure for institutional clients.</p>
        <p>UPDATE (Nov. 17, 12:35 UTC): Adds dropped words to first paragraph.</p>
      </div>
    </div>
    <div class="document-body font-body-lg font-sans font-metadata">
      <p>Disclosure &amp; Polices : CoinDesk is an award-winning media outlet that covers the cryptocurrency industry.</p>
    </div>
    <div id="article-bottom-news" data-module-name="article-bottom-news">
      <p>Diversified RWA stablecoins sustain 5-7% yield from real credit as crypto funding compresses to ~4%.</p>
    </div>
  </main>
</body>
</html>
"""


class TestCoinDeskCrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_coindesk_url("https://www.coindesk.com/business/2026/11/17/solana-coingecko"))
        self.assertTrue(is_coindesk_url("https://coindesk.com/tech/2026/10/28/google-crypto"))
        self.assertFalse(is_coindesk_url("https://www.semafor.com/article/11/17/2026/nvidia"))

    def test_multi_document_body_dedup_and_cleanup(self):
        res = crawl_coindesk(
            "https://www.coindesk.com/business/2026/11/17/solana-coingecko",
            html_text=SAMPLE_COINDESK_HTML,
            localize_cover=False,
            use_cache=False,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Solana Foundation takes majority stake in CoinGecko")
        self.assertEqual(res["author"], "Francisco Rodrigues and Helene Braun")
        self.assertEqual(res["published_at"], "2026-11-17T11:29:51.809Z")
        self.assertIn("### Expanding market infrastructure", res["full_text"])
        self.assertIn("foundation said it plans to bring trading to CoinGecko", res["full_text"])
        self.assertNotIn("Summary bullet", res["full_text"])
        self.assertNotIn("Read more:", res["full_text"])
        self.assertNotIn("Disclosure & Polices", res["full_text"])
        self.assertNotIn("Diversified RWA stablecoins", res["full_text"])
        self.assertNotIn("Adds dropped words", res["full_text"])
        # Exactly 1 inline image (cover duplicate stripped), full-res data-image-src used, Enlarge image stripped
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertEqual(
            res["inline_images"][0]["url"],
            "https://cdn.sanity.io/images/s3y3vcno/production/chart-1390x818.png?auto=format",
        )
        self.assertEqual(res["inline_images"][0]["after_para"], 1)
        self.assertFalse(res["inline_images"][0]["caption"].startswith("Enlarge image"))


if __name__ == "__main__":
    unittest.main()
