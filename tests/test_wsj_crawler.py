import unittest
from crawlers.wsj_crawler import (
    crawl_wsj,
    is_wsj_url,
    _clean_wsj_title,
    _clean_wsj_paragraph,
    _extract_techmeme_author,
    _is_valid_wsj_image,
    _strip_wayback_prefix,
)
from article_extractor import ArticleExtractor


class TestWsjCrawler(unittest.TestCase):
    def test_is_wsj_url(self):
        self.assertTrue(is_wsj_url("https://www.wsj.com/business/sec-is-probing-nvidia-amid-departure-of-ceo-jensen-huang-ee7643f8"))
        self.assertTrue(is_wsj_url("https://wsj.com/finance/corporate-card-startup-ramp-631b071a"))
        self.assertFalse(is_wsj_url("https://www.reuters.com/world/china/ai/"))
        self.assertFalse(is_wsj_url("https://www.bloomberg.com/news/articles/2026-11-16/tech"))
        self.assertFalse(is_wsj_url("https://fortune.com/2026/11/16/ai/"))

    def test_title_author_and_ticker_cleaning(self):
        self.assertEqual(
            _clean_wsj_title("Exclusive | SEC Is Probing Nvidia Amid Departure of CEO Jensen Huang - WSJ"),
            "SEC Is Probing Nvidia Amid Departure of CEO Jensen Huang"
        )
        self.assertEqual(
            _extract_techmeme_author("Sources: Ramp is in talks to raise $1B (Kate Clark/Wall Street Journal)"),
            "Kate Clark"
        )
        dirty_p = "The SEC is investigating Nvidia NVDA -0.44%decrease; down pointing triangle, whose CEO recently departed."
        cleaned = _clean_wsj_paragraph(dirty_p)
        self.assertNotIn("decrease; down pointing triangle", cleaned)
        self.assertIn("investigating Nvidia", cleaned)
        self.assertEqual(_clean_wsj_paragraph("Copyright ©2026 Dow Jones & Company, Inc. All Rights Reserved."), "")

    def test_image_validation_and_wayback_strip(self):
        self.assertEqual(
            _strip_wayback_prefix("https://web.archive.org/web/20261117210938im_/https://images.wsj.net/im-02933754/social"),
            "https://images.wsj.net/im-02933754/social"
        )
        self.assertTrue(_is_valid_wsj_image("https://images.wsj.net/im-02933754/social"))
        self.assertFalse(_is_valid_wsj_image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485"))
        self.assertFalse(_is_valid_wsj_image("https://s.tradingview.com/static/images/illustrations/news-story.png"))
        self.assertFalse(_is_valid_wsj_image("/relative/path.jpg"))

    def test_crawl_wsj_from_html_and_routing(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="Exclusive | AI Chip Probe Expands Across Cloud Providers - WSJ" />
            <meta property="og:image" content="https://images.wsj.net/sample_cover.jpg" />
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": "Exclusive | AI Chip Probe Expands Across Cloud Providers",
                "author": [{"@type": "Person", "name": "Robbie Whelan"}, {"@type": "Person", "name": "Kate Clark"}],
                "image": "https://images.wsj.net/sample_cover.jpg"
            }
            </script>
        </head>
        <body>
            <article>
                <p><style>.css-1{color:red;}</style>Federal regulators have expanded their inquiry into cloud AI chip disclosures at major semiconductor firms.</p>
                <p>According to people familiar with the matter, investigators requested internal communications covering overseas data center leases.</p>
                <p>Shares of Nvidia NVDA -0.44%decrease; down pointing triangle traded lower in morning trading following the regulatory disclosure.</p>
                <p>Copyright ©2026 Dow Jones & Company, Inc. All Rights Reserved.</p>
            </article>
        </body>
        </html>
        """
        url = "https://www.wsj.com/business/sample-story-1234abcd"
        res = ArticleExtractor.extract_article(url, html_text=sample_html)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "AI Chip Probe Expands Across Cloud Providers")
        self.assertEqual(res["author"], "Robbie Whelan and Kate Clark")
        self.assertEqual(res["cover_image"], "https://images.wsj.net/sample_cover.jpg")
        self.assertEqual(res["image_url"], "https://images.wsj.net/sample_cover.jpg")
        self.assertEqual(len(res["paragraphs"]), 3)
        self.assertEqual(res["article_content"], res["full_text"])
        self.assertEqual(res["article_content_en"], res["full_text"])
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertNotIn("down pointing triangle", res["full_text"])
        self.assertNotIn("Dow Jones & Company", res["full_text"])


if __name__ == "__main__":
    unittest.main()
